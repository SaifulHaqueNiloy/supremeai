package com.supremeai.controller;

import com.supremeai.service.SelfHealingService;
import com.supremeai.healing.AutoHealingEngine;
import com.supremeai.intelligence.healing.InfiniteAutoHealer;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Map;
import java.util.List;

@RestController
@RequestMapping("/api/self-healing")
@CrossOrigin(origins = "*")
public class SelfHealingController {

    private final SelfHealingService selfHealingService;

    public SelfHealingController(SelfHealingService selfHealingService) {
        this.selfHealingService = selfHealingService;
    }

    // ===== RETRY WITH BACKOFF =====

    @PostMapping("/retry")
    public ResponseEntity<Map<String, Object>> executeWithRetry(@RequestBody Map<String, Object> request) {
        int maxAttempts = (int) request.getOrDefault("maxAttempts", 3);
        long initialBackoff = ((Number) request.getOrDefault("initialBackoff", 1000L)).longValue();
        String taskName = (String) request.getOrDefault("taskName", "unknown");

        try {
            String result = selfHealingService.executeWithRetry(
                    () -> Mono.just("Task " + taskName + " completed successfully"),
                    maxAttempts,
                    initialBackoff
            ).block();

            return ResponseEntity.ok(Map.of(
                    "status", "success",
                    "result", result,
                    "maxAttempts", maxAttempts
            ));
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                    "status", "failed",
                    "error", e.getMessage(),
                    "maxAttempts", maxAttempts
            ));
        }
    }

    // ===== AUTO DETECTION AND FIX =====

    @PostMapping("/detect")
    public ResponseEntity<Map<String, Object>> detectAndFix(@RequestBody Map<String, String> request) {
        String error = request.get("error");
        if (error == null || error.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "Missing 'error' field"));
        }
        return ResponseEntity.ok(selfHealingService.detectAndFix(error));
    }

    // ===== INFINITE AUTO-HEALER =====

    @PostMapping("/develop")
    public ResponseEntity<Map<String, String>> developUntilPerfection(@RequestBody Map<String, String> request) {
        String taskCategory = request.getOrDefault("taskCategory", "general");
        String prompt = request.get("prompt");
        if (prompt == null || prompt.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "Missing 'prompt' field"));
        }
        try {
            String result = selfHealingService.developUntilPerfection(taskCategory, prompt);
            return ResponseEntity.ok(Map.of("status", "success", "code", result));
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of("status", "failed", "error", e.getMessage()));
        }
    }

    @GetMapping("/history")
    public Mono<ResponseEntity<Iterable<com.supremeai.model.HealingEvent>>> getHistory() {
        return selfHealingService.getHealingHistory()
                .collectList()
                .map(ResponseEntity::ok);
    }

    @PostMapping("/health-check")
    public Mono<ResponseEntity<Iterable<com.supremeai.model.APIHealthReport>>> runHealthCheck() {
        return selfHealingService.runProactiveHealthCheck()
                .map(report -> ResponseEntity.ok((Iterable<com.supremeai.model.APIHealthReport>) List.of(report)));
    }

    // ===== STATUS =====

    @GetMapping("/status")
    public ResponseEntity<Map<String, String>> getStatus() {
        return ResponseEntity.ok(Map.of(
                "status", "active",
                "service", "SelfHealingService",
                "autoHealing", "enabled",
                "infiniteLoop", "enabled",
                "auditTrail", "active",
                "aiAnalysis", "enabled"
        ));
    }
}
