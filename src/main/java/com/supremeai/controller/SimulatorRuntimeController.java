package com.supremeai.controller;

import com.supremeai.model.UserSimulatorProfile;
import com.supremeai.model.GeneratedApp;
import com.supremeai.service.SimulatorDeploymentService;
import com.supremeai.service.SimulatorService;
import com.supremeai.service.DeviceEmulationService;
import com.supremeai.service.SimulatorSessionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.*;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import java.net.URI;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Simulator Runtime Controller - Serves generated apps with device emulation.
 *
 * This is the ACTUAL runtime that serves preview URLs.
 */
@RestController
@RequestMapping("/simulator/preview")
public class SimulatorRuntimeController {

    private static final Logger logger = LoggerFactory.getLogger(SimulatorRuntimeController.class);

    @Autowired
    private SimulatorService simulatorService;

    @Autowired
    private SimulatorDeploymentService deploymentService;

    @Autowired
    private DeviceEmulationService deviceEmulationService;

    @Autowired
    private SimulatorSessionService sessionService;

    /**
     * GET /simulator/preview/{appId}
     * Main entry point: Serves the generated web app with device emulation applied.
     */
    @GetMapping("/{appId}")
    public Mono<ResponseEntity<byte[]>> servePreview(
            @PathVariable String appId,
            @RequestParam(defaultValue = "PIXEL_6") String device,
            ServerWebExchange exchange) {

        logger.info("[RUNTIME] Serving preview for app={} device={}", appId, device);

        // 1. Validate deployment exists
        SimulatorDeploymentService.DeploymentRecord record =
                deploymentService.getDeploymentRecord(appId);

        if (record == null || record.getStatus() != SimulatorDeploymentService.DeploymentStatus.RUNNING) {
            return Mono.just(ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(("Application not found or not running: " + appId).getBytes()));
        }

        // 2. Fetch generated app from Firestore
        return simulatorService.getGeneratedApp(appId)
                .switchIfEmpty(Mono.error(new RuntimeException("Generated app not found: " + appId)))
                .flatMap(app -> {
                    // 3. Apply device emulation
                    DeviceEmulationService.EmulationContext context =
                            deviceEmulationService.createContext(device);

                    byte[] transformedHtmlBytes = deviceEmulationService.transformHtml(
                            app.getHtmlContent().getBytes(),
                            context
                    );

                    // 4. Prepare HTTP response with device-specific headers
                    HttpHeaders headers = new HttpHeaders();
                    headers.setContentType(MediaType.TEXT_HTML);
                    headers.set("X-Device-Emulation", device);
                    headers.set("X-App-Version", app.getVersion());
                    headers.set("Cache-Control", "no-cache, no-store, must-revalidate");

                    // Inject runtime scripts for WebSocket control
                    String sessionId = sessionService.registerSession(appId, device);
                    String websocketUrl = "/ws/simulator/runtime/" + sessionId;

                    String injectedJs = String.format(
                            "<script>\n" +
                            "  (function() {\n" +
                            "    const config = {\n" +
                            "      appId: '%s',\n" +
                            "      device: '%s',\n" +
                            "      sessionId: '%s',\n" +
                            "      wsUrl: '%s'\n" +
                            "    };\n" +
                            "    window.__SIMULATOR__ = config;\n" +
                            "\n" +
                            "    // 1. Establish WebSocket Connection\n" +
                            "    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';\n" +
                            "    const wsFullUrl = protocol + '//' + window.location.host + config.wsUrl;\n" +
                            "    const socket = new WebSocket(wsFullUrl);\n" +
                            "\n" +
                            "    socket.onopen = () => {\n" +
                            "      console.log('[Simulator] Connected to control channel');\n" +
                            "      socket.send(JSON.stringify({ type: 'status', data: 'ready', timestamp: new Date().toISOString() }));\n" +
                            "    };\n" +
                            "\n" +
                            "    socket.onmessage = (event) => {\n" +
                            "      try {\n" +
                            "        const msg = JSON.parse(event.data);\n" +
                            "        if (msg.type === 'command') {\n" +
                            "          console.log('[Simulator] Executing command:', msg.data);\n" +
                            "          switch(msg.data) {\n" +
                            "            case 'back': window.history.back(); break;\n" +
                            "            case 'home': window.location.reload(); break;\n" +
                            "            case 'forward': window.history.forward(); break;\n" +
                            "          }\n" +
                            "        }\n" +
                            "      } catch (e) {\n" +
                            "        console.error('[Simulator] Failed to parse command', e);\n" +
                            "      }\n" +
                            "    };\n" +
                            "\n" +
                            "    // 2. Log Forwarding\n" +
                            "    const originalLog = console.log;\n" +
                            "    const originalError = console.error;\n" +
                            "    const originalWarn = console.warn;\n" +
                            "\n" +
                            "    const forwardLog = (level, args) => {\n" +
                            "      const message = Array.from(args).map(arg => \n" +
                            "        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)\n" +
                            "      ).join(' ');\n" +
                            "      \n" +
                            "      if (socket.readyState === WebSocket.OPEN) {\n" +
                            "        socket.send(JSON.stringify({\n" +
                            "          type: 'log',\n" +
                            "          level: level,\n" +
                            "          message: message,\n" +
                            "          timestamp: new Date().toISOString()\n" +
                            "        }));\n" +
                            "      }\n" +
                            "    };\n" +
                            "\n" +
                            "    console.log = function() { originalLog.apply(console, arguments); forwardLog('info', arguments); };\n" +
                            "    console.error = function() { originalError.apply(console, arguments); forwardLog('error', arguments); };\n" +
                            "    console.warn = function() { originalWarn.apply(console, arguments); forwardLog('warn', arguments); };\n" +
                            "\n" +
                            "    window.onerror = function(message, source, lineno, colno, error) {\n" +
                            "      forwardLog('error', [`Runtime Error: ${message} at ${source}:${lineno}:${colno}`]);\n" +
                            "    };\n" +
                            "\n" +
                            "    // 3. Notify Parent Dashboard\n" +
                            "    if (window.parent !== window) {\n" +
                            "      window.parent.postMessage({\n" +
                            "        source: 'supremeai-simulator',\n" +
                            "        type: 'ready',\n" +
                            "        data: config\n" +
                            "      }, '*');\n" +
                            "    }\n" +
                            "  })();\n" +
                            "</script>\n",
                            appId, device, sessionId, websocketUrl
                    );

                    String htmlContent = new String(transformedHtmlBytes);
                    if (htmlContent.contains("</head>")) {
                        htmlContent = htmlContent.replace("</head>", injectedJs + "</head>");
                    } else {
                        htmlContent = injectedJs + htmlContent;
                    }

                    logger.debug("[RUNTIME] Served app={} session={}", appId, sessionId);
                    return Mono.just(ResponseEntity.ok()
                            .headers(headers)
                            .body(htmlContent.getBytes()));
                });
    }

    /**
     * GET /simulator/preview/{appId}/health
     */
    @GetMapping("/{appId}/health")
    public Mono<ResponseEntity<Map<String, Object>>> healthCheck(@PathVariable String appId) {
        SimulatorDeploymentService.DeploymentRecord record =
                deploymentService.getDeploymentRecord(appId);

        boolean isHealthy = record != null &&
                record.getStatus() == SimulatorDeploymentService.DeploymentStatus.RUNNING;

        Map<String, Object> payload = Map.of(
                "status", isHealthy ? "HEALTHY" : "UNHEALTHY",
                "appId", appId,
                "timestamp", LocalDateTime.now().toString(),
                "activeSessions", sessionService.getActiveSessionCount()
        );

        HttpStatus status = isHealthy ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;
        return Mono.just(ResponseEntity.status(status).body(payload));
    }

    /**
     * Receive remote control command (alternative to WebSocket).
     */
    @PostMapping("/{appId}/control")
    public Mono<ResponseEntity<Map<String, Object>>> sendControlCommand(
            @PathVariable String appId,
            @RequestBody Map<String, Object> command) {

        String sessionId = (String) command.get("sessionId");
        if (sessionId == null) {
            return Mono.just(ResponseEntity.badRequest()
                    .body(Map.of("error", "sessionId required")));
        }

        SimulatorSessionService.RuntimeSession session = sessionService.getSession(sessionId);
        if (session == null || !session.getAppId().equals(appId)) {
            return Mono.just(ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Session not found")));
        }

        logger.info("[RUNTIME] Control command for session {}: {}", sessionId, command);

        return Mono.just(ResponseEntity.ok(Map.of(
                "received", true,
                "sessionId", sessionId,
                "timestamp", LocalDateTime.now().toString()
        )));
    }

    /**
     * Capture screenshot of current simulator state.
     */
    @GetMapping("/{appId}/screenshot")
    public Mono<ResponseEntity<Resource>> screenshot(
            @PathVariable String appId,
            @RequestParam(defaultValue = "png") String format) {

        return simulatorService.getGeneratedApp(appId)
                .map(app -> {
                    byte[] image = app.getScreenshot();
                    if (image == null || image.length == 0) {
                        image = new byte[]{
                                (byte)0x89,(byte)0x50,(byte)0x4E,(byte)0x47,(byte)0x0D,(byte)0x0A,(byte)0x1A,(byte)0x0A,
                                (byte)0x00,(byte)0x00,(byte)0x00,(byte)0x0D,(byte)0x49,(byte)0x48,(byte)0x44,(byte)0x52,
                                (byte)0x00,(byte)0x00,(byte)0x00,(byte)0x01,(byte)0x00,(byte)0x00,(byte)0x00,(byte)0x01,
                                (byte)0x08,(byte)0x06,(byte)0x00,(byte)0x00,(byte)0x00,(byte)0x1F,(byte)0x15,(byte)0xC4,
                                (byte)0x89,(byte)0x00,(byte)0x00,(byte)0x00,(byte)0x0A,(byte)0x49,(byte)0x44,(byte)0x41,
                                (byte)0x54,(byte)0x78,(byte)0x9C,(byte)0x63,(byte)0x00,(byte)0x01,(byte)0x00,(byte)0x00,
                                (byte)0x05,(byte)0x00,(byte)0x01,(byte)0x0D,(byte)0x0A,(byte)0x2D,(byte)0xB4,(byte)0x00,
                                (byte)0x00,(byte)0x00,(byte)0x00,(byte)0x49,(byte)0x45,(byte)0x4E,(byte)0x44,(byte)0xAE,
                                (byte)0x42,(byte)0x60,(byte)0x82
                        };
                    }

                    ByteArrayResource resource = new ByteArrayResource(image);
                    HttpHeaders headers = new HttpHeaders();
                    headers.setContentType(MediaType.parseMediaType("image/" + format));
                    headers.setCacheControl(CacheControl.noCache().getHeaderValue());

                    // Cast to Resource to match return type
                    return new ResponseEntity<>((Resource)resource, headers, HttpStatus.OK);
                })
                .defaultIfEmpty(ResponseEntity.<Resource>notFound().build());
    }

    /**
     * Stream console logs from the running simulator app.
     */
    @GetMapping(value="/{appId}/logs", produces=MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> streamLogs(
            @PathVariable String appId,
            @RequestParam(required=false) String level) {

        return Flux.interval(java.time.Duration.ofSeconds(1))
                .map(seq -> ServerSentEvent.<String>builder()
                        .event("log")
                        .id(String.valueOf(seq))
                        .data("[Simulator] Log stream placeholder - " + LocalDateTime.now())
                        .build());
    }

    /**
     * Proxy API requests from the simulated app to the actual backend.
     */
    @RequestMapping(path="/{appId}/api/**")
    public Mono<ResponseEntity<byte[]>> proxyApi(
            @PathVariable String appId,
            ServerWebExchange exchange) {

        String path = extractForwardedPath(exchange);
        logger.info("[RUNTIME] Proxying API request for app={}: /api/{}", appId, path);

        // Forward to the internal API on the same host/port
        String scheme = exchange.getRequest().getURI().getScheme();
        String host = exchange.getRequest().getURI().getHost();
        int port = exchange.getRequest().getURI().getPort();
        
        String targetUrl = scheme + "://" + host + (port != -1 ? ":" + port : "") + "/api/" + path;

        return WebClient.create().method(exchange.getRequest().getMethod())
                .uri(targetUrl)
                .headers(headers -> {
                    exchange.getRequest().getHeaders().forEach((k, v) -> {
                        if (!k.equalsIgnoreCase("Host") && !k.equalsIgnoreCase("Content-Length")) {
                            headers.addAll(k, v);
                        }
                    });
                })
                .body(exchange.getRequest().getBody(), byte[].class)
                .exchangeToMono(response -> response.toEntity(byte[].class));
    }

    private String extractForwardedPath(ServerWebExchange exchange) {
        String fullPath = exchange.getRequest().getPath().value();
        // Path is like /simulator/preview/app123/api/users
        String marker = "/api/";
        int idx = fullPath.indexOf(marker);
        if (idx != -1) {
            return fullPath.substring(idx + marker.length());
        }
        return "";
    }
}
