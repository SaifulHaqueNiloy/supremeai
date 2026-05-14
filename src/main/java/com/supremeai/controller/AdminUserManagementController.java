package com.supremeai.controller;

import com.supremeai.model.ActivityLog;
import com.supremeai.model.UserTier;
import com.supremeai.repository.ActivityLogRepository;
import com.supremeai.repository.UserRepository;
import com.supremeai.response.ApiResponse;
import com.supremeai.service.AdminDashboardFacadeService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import com.supremeai.dto.UserTierUpdateRequest;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

/**
 * AdminUserManagementController - Handles user-related admin tasks.
 */
@RestController
@RequestMapping("/api/admin/users")
public class AdminUserManagementController extends BaseAdminController<Object, String> {

    private static final Logger log = LoggerFactory.getLogger(AdminUserManagementController.class);

    private final UserRepository userRepository;
    private final ActivityLogRepository activityLogRepository;
    private final AdminDashboardFacadeService facadeService;

    @Autowired
    public AdminUserManagementController(UserRepository userRepository,
                                          ActivityLogRepository activityLogRepository,
                                          AdminDashboardFacadeService facadeService) {
        this.userRepository = userRepository;
        this.activityLogRepository = activityLogRepository;
        this.facadeService = facadeService;
    }

    @GetMapping
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> getUsers() {
        return wrapList(
                userRepository.findAll().map(facadeService::toUserMap),
                "users"
        );
    }

    @PutMapping("/{userId}/tier")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> updateUserTier(@PathVariable String userId,
                                                                                 @Valid @RequestBody UserTierUpdateRequest request) {
        UserTier newTier = UserTier.valueOf(request.getTier().toUpperCase());

        return org.springframework.security.core.context.ReactiveSecurityContextHolder.getContext()
                .map(org.springframework.security.core.context.SecurityContext::getAuthentication)
                .flatMap(auth -> {
                    String adminUserId = auth.getName();
                    return userRepository.findById(userId)
                            .flatMap(user -> {
                                String oldTier = user.getTier().toString();
                                user.setTier(newTier);
                                user.setUpdatedAt(LocalDateTime.now().toString());
                                return userRepository.save(user)
                                        .flatMap(savedUser -> {
                                            com.supremeai.model.ActivityLog logEntry = new com.supremeai.model.ActivityLog();
                                            logEntry.setUser(adminUserId);
                                            logEntry.setAction("UPDATE_USER_TIER");
                                            logEntry.setCategory("USER_MANAGEMENT");
                                            logEntry.setSeverity("INFO");
                                            logEntry.setOutcome("SUCCESS");
                                            logEntry.setDetails("Changed user " + userId + " tier from " + oldTier + " to " + newTier);
                                            return activityLogRepository.save(logEntry).thenReturn(savedUser);
                                        });
                            })
                            .map(user -> ResponseEntity.ok(ApiResponse.ok(Map.of(
                                    "message", "User tier updated successfully",
                                    "user", Map.of(
                                            "id", user.getFirebaseUid(),
                                            "tier", user.getTier().toString(),
                                            "monthlyQuota", user.fetchMonthlyQuota()
                                    )
                            ))))
                            .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.error("User not found")));
                })
                .onErrorResume(e -> Mono.just(ResponseEntity.status(500).body(ApiResponse.error("Failed to update user tier: " + e.getMessage()))));
    }

    @GetMapping("/tiers")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> getAvailableTiers() {
        return Mono.fromCallable(() -> {
            List<Map<String, Object>> tiers = java.util.stream.Stream.of(UserTier.values())
                    .map(tier -> {
                        Map<String, Object> tierMap = new HashMap<>();
                        tierMap.put("name", tier.name());
                        tierMap.put("displayName", tier.name().charAt(0) + tier.name().substring(1).toLowerCase());
                        tierMap.put("monthlyQuota", tier.getDefaultMonthlyQuota());
                        tierMap.put("description", tier.getDescription());
                        tierMap.put("hasUnlimitedQuota", tier.hasUnlimitedQuota());
                        return tierMap;
                    }).toList();
            return ResponseEntity.ok(ApiResponse.ok(Map.<String, Object>of("tiers", tiers)));
        }).subscribeOn(reactor.core.scheduler.Schedulers.boundedElastic());
    }
}
