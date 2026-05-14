package com.supremeai.controller;

import com.supremeai.service.CyberSecuritySkillService;
import com.supremeai.response.ApiResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Map;
import java.util.List;

/**
 * Controller for the system's autonomous cyber security skills.
 * Handles self-audits, defensive learning cycles, and protection status.
 */
@RestController
@RequestMapping("/api/admin/security/cyber")
@PreAuthorize("hasRole('ADMIN')")
public class CyberSecurityController {

    @Autowired
    private CyberSecuritySkillService cyberSecuritySkillService;

    @GetMapping("/skills")
    public reactor.core.publisher.Flux<Map<String, Object>> getSkills() {
        return cyberSecuritySkillService.getLearnedSkills();
    }

    @GetMapping("/protections")
    public reactor.core.publisher.Flux<Map<String, Object>> getProtections() {
        return cyberSecuritySkillService.getActiveProtections();
    }

    @PostMapping("/learn")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> initiateLearning(@RequestBody Map<String, String> body) {
        String topic = body.getOrDefault("topic", "General Vulnerabilities");
        return cyberSecuritySkillService.initiateLearningCycle(topic)
                .map(insight -> ResponseEntity.ok(ApiResponse.ok(insight)));
    }

    @PostMapping("/audit")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> runAudit() {
        return cyberSecuritySkillService.runSelfAudit()
                .map(report -> ResponseEntity.ok(ApiResponse.ok(report)));
    }
}
