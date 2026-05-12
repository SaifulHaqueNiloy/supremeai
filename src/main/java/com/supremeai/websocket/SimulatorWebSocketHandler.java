package com.supremeai.websocket;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.supremeai.service.SimulatorSessionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Simulator WebSocket Handler - Bridges communication between the Admin Dashboard 
 * and the running Simulator instances.
 */
@Component
public class SimulatorWebSocketHandler extends TextWebSocketHandler {

    private static final Logger logger = LoggerFactory.getLogger(SimulatorWebSocketHandler.class);
    private final Gson gson = new Gson();

    @Autowired
    private SimulatorSessionService sessionService;

    // sessionId -> Set of WebSocketSessions (one for runtime, one or more for dashboard)
    private final Map<String, WebSocketSession> runtimeSessions = new ConcurrentHashMap<>();
    private final Map<String, ConcurrentHashMap.KeySetView<WebSocketSession, Boolean>> dashboardSessions = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        String path = session.getUri().getPath();
        logger.info("[WS_SIMULATOR] Connection established: {} path={}", session.getId(), path);

        // Path format: /ws/simulator/runtime/{sessionId} OR /ws/simulator/dashboard/{sessionId}
        String[] parts = path.split("/");
        if (parts.length < 5) {
            logger.warn("[WS_SIMULATOR] Invalid connection path: {}", path);
            session.close(CloseStatus.BAD_DATA);
            return;
        }

        String type = parts[3]; // runtime or dashboard
        String sessionId = parts[4];

        if ("runtime".equals(type)) {
            runtimeSessions.put(sessionId, session);
            logger.info("[WS_SIMULATOR] Registered RUNTIME session: {} for simulator={}", session.getId(), sessionId);
        } else if ("dashboard".equals(type)) {
            dashboardSessions.computeIfAbsent(sessionId, k -> ConcurrentHashMap.newKeySet()).add(session);
            logger.info("[WS_SIMULATOR] Registered DASHBOARD session: {} for simulator={}", session.getId(), sessionId);
        }

        sessionService.refreshHeartbeat(sessionId);
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        String path = session.getUri().getPath();
        String[] parts = path.split("/");
        String type = parts[3];
        String sessionId = parts[4];

        sessionService.refreshHeartbeat(sessionId);

        if ("runtime".equals(type)) {
            // Message from Simulator Runtime -> Broadcast to Dashboards
            broadcastToDashboards(sessionId, payload);
        } else if ("dashboard".equals(type)) {
            // Message from Dashboard -> Send to Simulator Runtime
            sendToRuntime(sessionId, payload);
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        String path = session.getUri().getPath();
        String[] parts = path.split("/");
        if (parts.length >= 5) {
            String type = parts[3];
            String sessionId = parts[4];

            if ("runtime".equals(type)) {
                runtimeSessions.remove(sessionId);
                logger.info("[WS_SIMULATOR] RUNTIME session closed: {}", sessionId);
            } else if ("dashboard".equals(type)) {
                var sessions = dashboardSessions.get(sessionId);
                if (sessions != null) {
                    sessions.remove(session);
                    if (sessions.isEmpty()) {
                        dashboardSessions.remove(sessionId);
                    }
                }
                logger.info("[WS_SIMULATOR] DASHBOARD session closed: {}", sessionId);
            }
        }
    }

    private void broadcastToDashboards(String sessionId, String payload) {
        var sessions = dashboardSessions.get(sessionId);
        if (sessions != null) {
            TextMessage message = new TextMessage(payload);
            sessions.forEach(s -> {
                try {
                    if (s.isOpen()) {
                        s.sendMessage(message);
                    }
                } catch (IOException e) {
                    logger.warn("[WS_SIMULATOR] Failed to send message to dashboard: {}", s.getId());
                }
            });
        }
    }

    private void sendToRuntime(String sessionId, String payload) {
        WebSocketSession runtimeSession = runtimeSessions.get(sessionId);
        if (runtimeSession != null && runtimeSession.isOpen()) {
            try {
                runtimeSession.sendMessage(new TextMessage(payload));
            } catch (IOException e) {
                logger.warn("[WS_SIMULATOR] Failed to send message to runtime: {}", sessionId);
            }
        } else {
            logger.warn("[WS_SIMULATOR] No active runtime session for {}. Dropping command.", sessionId);
        }
    }
}
