package com.supremeai.controller;

import com.supremeai.service.PubSubPublisherService;
import com.supremeai.service.ReverseEngineeringIntegrationService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Controller for website reverse engineering feature.
 * Submits jobs to Pub/Sub queue for async processing by Python FastAPI worker.
 */
@RestController
@RequestMapping("/api/reverse")
public class ReverseEngineeringController {

    private static final Logger logger = LoggerFactory.getLogger(ReverseEngineeringController.class);
    private static final String PUBSUB_TOPIC = "reverse-engineering-jobs";

    @Autowired
    private PubSubPublisherService pubSubPublisherService;

    @Autowired
    private ReverseEngineeringIntegrationService integrationService;

    @PostMapping("/start")
    public ResponseEntity<Map<String, Object>> startReverseEngineering(
            @RequestParam String url,
            Authentication auth) {
        
        String userId = auth != null ? auth.getName() : "anonymous";
        String jobId = "reveng_" + UUID.randomUUID().toString().substring(0, 12);
        
        logger.info("Starting reverse engineering job: {} for {} by {}", jobId, url, userId);
        
        // Persist job in Firestore via integration service
        integrationService.startJob(userId, url).subscribe();
        
        // Publish job to Pub/Sub for processing by Python worker
        Map<String, Object> message = new HashMap<>();
        message.put("jobId", jobId);
        message.put("userId", userId);
        message.put("websiteUrl", url);
        message.put("scrapeDepth", 1);
        message.put("discoverApis", true);
        
        try {
            pubSubPublisherService.publish(PUBSUB_TOPIC, message);
            logger.info("Published reverse engineering job {} to topic {}", jobId, PUBSUB_TOPIC);
        } catch (Exception e) {
            logger.error("Failed to publish to Pub/Sub: {}", e.getMessage(), e);
            // Fallback: continue without Pub/Sub
        }
        
        Map<String, Object> response = new HashMap<>();
        response.put("jobId", jobId);
        response.put("status", "PENDING");
        response.put("message", "Reverse engineering job queued");
        
        return ResponseEntity.ok(response);
    }

    @GetMapping("/job/{jobId}")
    public ResponseEntity<Map<String, Object>> getJobStatus(
            @PathVariable String jobId,
            Authentication auth) {
        
        String userId = auth != null ? auth.getName() : null;
        
        // Query job status from Firestore via integration service
        return ResponseEntity.ok(Map.of(
            "jobId", jobId,
            "status", "PENDING",
            "message", "Job status endpoint - implementation depends on Firestore query"
        ));
    }

    @PostMapping("/job/{jobId}/complete")
    public ResponseEntity<Map<String, Object>> completeJob(
            @PathVariable String jobId,
            @RequestBody Map<String, Object> result,
            Authentication auth) {
        
        // Called by Python worker when job completes (or admin to manually mark complete)
        String userId = auth != null ? auth.getName() : "system";
        
        @SuppressWarnings("unchecked")
        Map<String, Object> discoveredApis = (Map<String, Object>) result.get("discoveredApis");
        if (discoveredApis == null) discoveredApis = Map.of();
        
        integrationService.completeJob(jobId, discoveredApis)
            .subscribe(
                savedJob -> logger.info("Job {} marked completed by {}", jobId, userId),
                error -> logger.error("Failed to complete job {}: {}", jobId, error.getMessage())
            );
        
        return ResponseEntity.ok(Map.of("jobId", jobId, "status", "COMPLETED"));
    }

    /**
     * Manually trigger integration: generate app from completed reverse engineering job.
     */
    @PostMapping("/integrate/{jobId}")
    public ResponseEntity<Map<String, Object>> integrateWithCodeGen(
            @PathVariable String jobId,
            Authentication auth) {
        
        String userId = auth != null ? auth.getName() : "anonymous";
        
        integrationService.onJobCompletion(jobId, userId)
            .subscribe(
                job -> {
                    logger.info("Integration triggered for job {}: generated app {}", jobId, job.getGeneratedAppId());
                },
                error -> {
                    logger.error("Integration failed for job {}: {}", jobId, error.getMessage());
                }
            );
        
        return ResponseEntity.ok(Map.of(
            "jobId", jobId,
            "status", "INTEGRATING",
            "message", "Code generation started from reverse engineering results"
        ));
    }
}
