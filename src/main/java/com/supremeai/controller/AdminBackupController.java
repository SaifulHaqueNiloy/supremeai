package com.supremeai.controller;

import com.supremeai.response.ApiResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/admin/backup")
public class AdminBackupController {

    private final List<Map<String, Object>> mockBackups = new ArrayList<>();

    public AdminBackupController() {
        // Initial mock data
        mockBackups.add(Map.of(
            "id", "bak-001",
            "name", "Full System Backup - May 10",
            "size", "45.2 MB",
            "timestamp", Instant.now().minusSeconds(172800).toString(),
            "status", "COMPLETED"
        ));
    }

    @GetMapping("/list")
    public Mono<ResponseEntity<ApiResponse<List<Map<String, Object>>>>> listBackups() {
        return Mono.just(ResponseEntity.ok(ApiResponse.ok(mockBackups)));
    }

    @PostMapping("/trigger")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> triggerBackup(@RequestBody Map<String, String> request) {
        String name = request.getOrDefault("name", "Manual Backup " + Instant.now().toString());
        Map<String, Object> newBackup = Map.of(
            "id", UUID.randomUUID().toString(),
            "name", name,
            "size", "Calculating...",
            "timestamp", Instant.now().toString(),
            "status", "IN_PROGRESS"
        );
        // In a real app, this would trigger an async service
        return Mono.just(ResponseEntity.ok(ApiResponse.ok(Map.of(
            "message", "Backup triggered successfully",
            "backup", newBackup
        ))));
    }

    @DeleteMapping("/{id}")
    public Mono<ResponseEntity<ApiResponse<String>>> deleteBackup(@PathVariable String id) {
        return Mono.just(ResponseEntity.ok(ApiResponse.ok("Backup " + id + " deleted successfully")));
    }
}
