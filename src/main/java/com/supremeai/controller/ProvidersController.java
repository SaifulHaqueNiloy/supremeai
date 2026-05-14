package com.supremeai.controller;

import com.supremeai.response.ApiResponse;
import com.supremeai.service.AIProviderDiscoveryService;
import com.supremeai.model.APIProvider;
import com.supremeai.model.ActivityLog;
import com.supremeai.repository.ProviderRepository;
import com.supremeai.repository.ActivityLogRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import com.supremeai.service.*;
import com.supremeai.model.*;
import com.supremeai.repository.*;
import com.supremeai.admin.AdminDashboardService;
import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api/admin/providers")
public class ProvidersController extends BaseAdminController<APIProvider, String> {

    private static final Logger log = LoggerFactory.getLogger(ProvidersController.class);

    @Autowired
    private ProviderRepository providerRepository;
    
    @Autowired
    private ActivityLogRepository activityLogRepository;

    @Autowired
    private AIProviderDiscoveryService discoveryService;

    private final AdminDashboardService adminDashboardService;
    private final ProviderRoleSuggestionService roleSuggestionService;
    private final AdminProviderValidationService adminProviderValidationService;

    @Autowired
    public ProvidersController(ProviderRepository providerRepository,
                             ActivityLogRepository activityLogRepository,
                             AdminDashboardService adminDashboardService,
                             ProviderRoleSuggestionService roleSuggestionService,
                             AdminProviderValidationService adminProviderValidationService) {
        this.providerRepository = providerRepository;
        this.activityLogRepository = activityLogRepository;
        this.adminDashboardService = adminDashboardService;
        this.roleSuggestionService = roleSuggestionService;
        this.adminProviderValidationService = adminProviderValidationService;
    }

    private String getCurrentAdminUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || auth.getName() == null) {
            throw new IllegalStateException("Not authenticated");
        }
        return auth.getName();
    }

        @GetMapping("/configured")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> getConfiguredProviders() {
        return wrapList(providerRepository.findAll(), "providers");
    }

    @PostMapping("/add")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> addProvider(@RequestBody APIProvider provider) {
        return validateBeforeSave(provider)
                .flatMap(valid -> {
                    if (!valid) {
                        return Mono.just(ResponseEntity.badRequest()
                                .body(ApiResponse.<Map<String, Object>>error("Invalid API key or provider unreachable")));
                    }
                    provider.setStatus("inactive"); // Default to inactive until admin activates
                    provider.setConsecutiveErrorDays(0);
                    provider.setLastValidated(LocalDateTime.now());
                    return updateProvider(provider);
                });
    }

    @PutMapping("/{id}")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>>
            updateProviderById(@PathVariable String id, @RequestBody APIProvider provider) {
        provider.setId(id);
        // If apiKey is being updated, re-validate
        return providerRepository.findById(id)
                .flatMap(existing -> {
                    boolean keyChanged = provider.getApiKey() != null &&
                            !provider.getApiKey().equals(existing.getApiKey());
                    if (keyChanged) {
                        return validateBeforeSave(provider).flatMap(valid -> {
                            if (!valid) {
                                return Mono.just(ResponseEntity.badRequest()
                                        .body(ApiResponse.<Map<String, Object>>error("Invalid API key or provider unreachable")));
                            }
                            // Reset error streak on key update
                            provider.setConsecutiveErrorDays(0);
                            provider.setLastValidated(LocalDateTime.now());
                            // If previously dead, revive on valid key update
                            if ("dead".equals(existing.getStatus()) || "error".equals(existing.getStatus())) {
                                provider.setStatus("active");
                                provider.setDeadReason(null);
                                provider.setDeadAt(null);
                                provider.setLastErrorDate(null);
                            }
                            return updateProvider(provider);
                        });
                    } else {
                        // Key unchanged, but handle status transitions
                        if ("inactive".equals(existing.getStatus()) && "active".equals(provider.getStatus())) {
                            // Admin manually activating: reset streak
                            provider.setConsecutiveErrorDays(0);
                            provider.setLastValidated(LocalDateTime.now());
                        }
                        return updateProvider(provider);
                    }
                })
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.<Map<String, Object>>error("Provider not found")));
    }

    /**
     * Validate API key using discovery service before persisting.
     * Returns true if valid, false otherwise.
     */
    private Mono<Boolean> validateBeforeSave(APIProvider provider) {
        if (provider.getApiKey() == null || provider.getType() == null) {
            return Mono.just(false);
        }
        return discoveryService.validateKey(provider.getType(), provider.getApiKey())
                .map(valid -> {
                    if (!valid) {
                        log.warn("API key validation failed for provider type '{}' (name: {})",
                                provider.getType(), provider.getName());
                    } else {
                        log.info("API key validated successfully for provider type '{}' (name: {})",
                                provider.getType(), provider.getName());
                    }
                    return valid;
                })
                .onErrorReturn(false);
    }

    @PostMapping("/{id}/revive")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> reviveProvider(@PathVariable String id) {
        String adminUserId = getCurrentAdminUserId();
        return providerRepository.findById(id)
                .flatMap(provider -> {
                    if (!"dead".equals(provider.getStatus()) && !"error".equals(provider.getStatus())) {
                        return Mono.just(ResponseEntity.badRequest()
                                .body(ApiResponse.<Map<String, Object>>error("Provider is not dead or in error state")));
                    }
                    provider.setStatus("active");
                    provider.setConsecutiveErrorDays(0);
                    provider.setDeadReason(null);
                    provider.setDeadAt(null);
                    provider.setLastErrorDate(null);
                    provider.setLastValidated(LocalDateTime.now());

                    return providerRepository.save(provider)
                            .flatMap(saved -> {
                                ActivityLog log = new ActivityLog();
                                log.setUser(adminUserId);
                                log.setAction("REVIVE_PROVIDER");
                                log.setCategory("PROVIDER_MANAGEMENT");
                                log.setSeverity("INFO");
                                log.setOutcome("SUCCESS");
                                log.setDetails("Revived provider: " + saved.getId() + " (" + saved.getName() + ")");
                                return activityLogRepository.save(log)
                                        .thenReturn(ResponseEntity.ok(ApiResponse.ok(Map.of(
                                                "message", "Provider revived successfully",
                                                "provider", saved
                                        ))));
                            });
                })
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.<Map<String, Object>>error("Provider not found")));
    }

    @PostMapping("/remove")
    public Mono<ResponseEntity<ApiResponse<String>>> removeProvider(@RequestBody Map<String, String> payload) {
        String providerId = payload.get("providerId");
        if (providerId == null) {
            return Mono.just(ResponseEntity.badRequest().body(ApiResponse.<String>error("providerId is required")));
        }
        return deleteProvider(providerId).map(re -> {
            boolean success = re.getBody() != null && re.getBody().success();
            String error = (re.getBody() != null) ? re.getBody().error() : "Unknown error";
            return ResponseEntity.status(re.getStatusCode()).body(success ? ApiResponse.ok("Provider removed") : ApiResponse.<String>error(error));
        });
    }

    @PostMapping("/test-key")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> testProviderKey(@RequestBody Map<String, String> payload) {
        String name = payload.get("name");
        String apiKey = payload.get("apiKey");

        if (name == null || apiKey == null) {
            return Mono.just(ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error("name and apiKey are required")));
        }

        return discoveryService.validateKey(name, apiKey)
                .map(valid -> {
                    if (valid) {
                        return ResponseEntity.ok(ApiResponse.ok(Map.<String, Object>of("message", "Key validated successfully", "valid", true)));
                    } else {
                        return ResponseEntity.status(401).body(ApiResponse.<Map<String, Object>>error("Invalid key or provider error"));
                    }
                });
    }

    @GetMapping("/discover")
    public Mono<ResponseEntity<ApiResponse<java.util.List<Map<String, Object>>>>> discoverModels(@RequestParam(required = false) String query) {
        return discoveryService.discoverModels(query)
                .collectList()
                .map(list -> ResponseEntity.ok(ApiResponse.ok(list)));
    }

    @GetMapping("/scan")
    public Mono<ResponseEntity<ApiResponse<java.util.List<Map<String, Object>>>>> scanDeployments() {
        return discoveryService.scanDeployments()
                .collectList()
                .map(list -> ResponseEntity.ok(ApiResponse.ok(list)));
    }

    @PostMapping
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> updateProvider(@RequestBody APIProvider provider) {
        String adminUserId = getCurrentAdminUserId();
        return providerRepository.save(provider)
                .flatMap(saved -> {
                    // Log admin action reactive way
                    ActivityLog log = new ActivityLog();
                    log.setUser(adminUserId);
                    log.setAction("UPDATE_PROVIDER");
                    log.setCategory("PROVIDER_MANAGEMENT");
                    log.setSeverity("INFO");
                    log.setOutcome("SUCCESS");
                    log.setDetails("Updated provider: " + saved.getId() + " (" + saved.getName() + ")");
                    
                    return activityLogRepository.save(log)
                            .thenReturn(ResponseEntity.ok(ApiResponse.ok(Map.of(
                                "message", "Provider updated successfully",
                                "provider", saved
                            ))));
                });
    }

    @DeleteMapping("/{id}")
    public Mono<ResponseEntity<ApiResponse<String>>> deleteProvider(@PathVariable String id) {
        String adminUserId = getCurrentAdminUserId();
        return providerRepository.findById(id)
                .flatMap(provider -> {
                    String providerName = provider.getName();
                    return providerRepository.deleteById(id)
                            .then(Mono.fromCallable(() -> {
                                ActivityLog log = new ActivityLog();
                                log.setUser(adminUserId);
                                log.setAction("DELETE_PROVIDER");
                                log.setCategory("PROVIDER_MANAGEMENT");
                                log.setSeverity("WARN");
                                log.setOutcome("SUCCESS");
                                log.setDetails("Deleted provider: " + id + " (" + providerName + ")");
                                return log;
                            }))
                            .flatMap(activityLogRepository::save)
                            .thenReturn(ResponseEntity.ok(ApiResponse.ok("Provider deleted")));
                })
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.<String>error("Provider not found")));
    }

    @GetMapping("/{id}/suggest-roles")
    public Mono<ResponseEntity<ApiResponse<List<String>>>> suggestRoles(@PathVariable String id) {
        return providerRepository.findById(id)
                .map(provider -> ResponseEntity.ok(ApiResponse.ok(roleSuggestionService.suggestRoles(provider))))
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.error("Provider not found")));
    }

    @PatchMapping("/{id}/capability")
    public Mono<ResponseEntity<ApiResponse<APIProvider>>> patchCapability(
            @PathVariable String id, 
            @RequestBody Map<String, Object> updates) {
        String adminUserId = getCurrentAdminUserId();
        return providerRepository.findById(id)
                .flatMap(provider -> {
                    if (updates.containsKey("canCommunicate")) {
                        provider.setCanCommunicate((Boolean) updates.get("canCommunicate"));
                    }
                    if (updates.containsKey("canExecuteTasks")) {
                        provider.setCanExecuteTasks((Boolean) updates.get("canExecuteTasks"));
                    }
                    if (updates.containsKey("canParticipateInVoting")) {
                        provider.setCanParticipateInVoting((Boolean) updates.get("canParticipateInVoting"));
                    }
                    if (updates.containsKey("assignedRoles")) {
                        @SuppressWarnings("unchecked")
                        List<String> roles = (List<String>) updates.get("assignedRoles");
                        provider.setAssignedRoles(roles);
                    }
                    
                    return providerRepository.save(provider)
                            .flatMap(saved -> {
                                ActivityLog log = new ActivityLog();
                                log.setUser(adminUserId);
                                log.setAction("UPDATE_CAPABILITY");
                                log.setCategory("PROVIDER_MANAGEMENT");
                                log.setSeverity("INFO");
                                log.setOutcome("SUCCESS");
                                log.setDetails("Updated capabilities/roles for provider: " + id);
                                return activityLogRepository.save(log).thenReturn(saved);
                            });
                })
                .map(saved -> ResponseEntity.ok(ApiResponse.ok(saved)))
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.<APIProvider>error("Provider not found")));
    }

    @PostMapping("/test-all")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> testAllProviders() {
        // This triggers the validation service manually in background
        Mono.fromRunnable(() -> adminProviderValidationService.validateAllActiveProviders())
                .subscribeOn(reactor.core.scheduler.Schedulers.boundedElastic())
                .subscribe(); // Run in background

        return Mono.just(ResponseEntity.ok(ApiResponse.ok(Map.of(
            "status", "validation_started",
            "message", "সিস্টেম সব কী চেক করা শুরু করেছে। কিছুক্ষণের মধ্যে রিপোর্ট আপডেট হবে।"
        ))));
    }

    @GetMapping("/health-stats")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> getHealthStats() {
        return providerRepository.findAll().collectList()
                .map(list -> {
                    long active = list.stream().filter(p -> "active".equals(p.getStatus())).count();
                    long error = list.stream().filter(p -> "error".equals(p.getStatus())).count();
                    long dead = list.stream().filter(p -> "dead".equals(p.getStatus())).count();
                    
                    return ResponseEntity.ok(ApiResponse.ok(Map.of(
                        "total", list.size(),
                        "active", active,
                        "error", error,
                        "dead", dead,
                        "healthScore", list.size() > 0 ? (active * 100 / list.size()) : 100
                    )));
                });
    }

    @DeleteMapping("/bulk-remove-dead")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> removeDeadProviders() {
        return providerRepository.findAll()
                .filter(p -> "dead".equals(p.getStatus()))
                .flatMap(p -> providerRepository.deleteById(p.getId()))
                .then(Mono.just(ResponseEntity.ok(ApiResponse.ok(Map.of(
                    "message", "সব ডেড কী সফলভাবে রিমুভ করা হয়েছে।"
                )))));
    }
}
