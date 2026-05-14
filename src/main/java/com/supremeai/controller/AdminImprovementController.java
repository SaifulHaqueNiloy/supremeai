package com.supremeai.controller;

import com.supremeai.admin.AdminDashboardService;
import com.supremeai.admin.ImprovementProposal;
import com.supremeai.response.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * AdminImprovementController - Handles system improvement proposals.
 */
@RestController
@RequestMapping("/api/admin/improvements")
public class AdminImprovementController {

    private static final Logger log = LoggerFactory.getLogger(AdminImprovementController.class);
    private final AdminDashboardService adminDashboardService;

    @Autowired
    public AdminImprovementController(AdminDashboardService adminDashboardService) {
        this.adminDashboardService = adminDashboardService;
    }

    @GetMapping("/pending")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> getPendingImprovements() {
        List<ImprovementProposal> pending = adminDashboardService.getPendingApprovals();
        return Mono.just(ResponseEntity.ok(ApiResponse.ok(Map.of(
                "pending", pending,
                "count", pending.size()
        ))));
    }

    @PostMapping("/approve/{proposalId}")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> approveProposal(@PathVariable String proposalId) {
        boolean success = adminDashboardService.approveProposal(proposalId);
        if (success) {
            return Mono.just(ResponseEntity.ok(ApiResponse.ok(Map.of(
                "status", "approved",
                "proposalId", proposalId
            ))));
        } else {
            return Mono.just(ResponseEntity.status(404).body(ApiResponse.error("Proposal not found", Map.of(
                "proposalId", proposalId
            ))));
        }
    }

    @PostMapping("/reject/{proposalId}")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> rejectProposal(@PathVariable String proposalId) {
        boolean success = adminDashboardService.rejectProposal(proposalId);
        if (success) {
            return Mono.just(ResponseEntity.ok(ApiResponse.ok(Map.of(
                "status", "rejected",
                "proposalId", proposalId
            ))));
        } else {
            return Mono.just(ResponseEntity.status(404).body(ApiResponse.error("Proposal not found", Map.of(
                "proposalId", proposalId
            ))));
        }
    }
}
