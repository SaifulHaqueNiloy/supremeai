package com.supremeai.controller;

import com.supremeai.response.ApiResponse;
import com.supremeai.model.APIProvider;
import com.supremeai.admin.ProviderAdminService;
import com.supremeai.service.AIProviderDiscoveryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * Controller for managing AI providers.
 * Refactored to delegate business logic to ProviderAdminService.
 */
@RestController
@RequestMapping("/api/admin/providers")
public class ProvidersController extends BaseAdminController<APIProvider, String> {

    private static final Logger log = LoggerFactory.getLogger(ProvidersController.class);

    private final ProviderAdminService providerAdminService;
    private final AIProviderDiscoveryService discoveryService;

    @Autowired
    public ProvidersController(ProviderAdminService providerAdminService,
                               AIProviderDiscoveryService discoveryService) {
        this.providerAdminService = providerAdminService;
        this.discoveryService = discoveryService;
    }

    private Mono<String> getCurrentAdminUserId() {
        return org.springframework.security.core.context.ReactiveSecurityContextHolder.getContext()
                .map(ctx -> ctx.getAuthentication().getName())
                .switchIfEmpty(Mono.error(new IllegalStateException("Not authenticated")));
    }

    @GetMapping("/configured")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> getConfiguredProviders() {
        return wrapList(providerAdminService.getAllProviders(), "providers");
    }

    @PostMapping("/add")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> addProvider(@RequestBody APIProvider provider) {
        return getCurrentAdminUserId()
                .flatMap(adminUserId -> providerAdminService.addProvider(provider, adminUserId))
                .map(saved -> ResponseEntity.ok(ApiResponse.ok(Map.of("message", "Provider added", "provider", (Object)saved))))
                .onErrorResume(e -> Mono.just(ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()))));
    }

    @PutMapping("/{id}")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>>
            updateProviderById(@PathVariable String id, @RequestBody APIProvider provider) {
        return getCurrentAdminUserId()
                .flatMap(adminUserId -> providerAdminService.updateProvider(id, provider, adminUserId))
                .map(saved -> ResponseEntity.ok(ApiResponse.ok(Map.of("message", "Provider updated", "provider", (Object)saved))))
                .onErrorResume(e -> Mono.just(ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()))))
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.error("Provider not found")));
    }

    @PostMapping("/{id}/revive")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> reviveProvider(@PathVariable String id) {
        return getCurrentAdminUserId()
                .flatMap(adminUserId -> providerAdminService.reviveProvider(id, adminUserId))
                .map(saved -> ResponseEntity.ok(ApiResponse.ok(Map.of("message", "Provider revived successfully", "provider", (Object)saved))))
                .onErrorResume(e -> Mono.just(ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()))))
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.error("Provider not found")));
    }

    @PostMapping("/remove")
    public Mono<ResponseEntity<ApiResponse<String>>> removeProvider(@RequestBody Map<String, String> payload) {
        String providerId = payload.get("providerId");
        if (providerId == null) {
            return Mono.just(ResponseEntity.badRequest().body(ApiResponse.error("providerId is required")));
        }
        return deleteProvider(providerId);
    }

    @DeleteMapping("/{id}")
    public Mono<ResponseEntity<ApiResponse<String>>> deleteProvider(@PathVariable String id) {
        return getCurrentAdminUserId()
                .flatMap(adminUserId -> providerAdminService.deleteProvider(id, adminUserId))
                .then(Mono.just(ResponseEntity.ok(ApiResponse.ok("Provider deleted"))))
                .onErrorResume(e -> Mono.just(ResponseEntity.status(500).body(ApiResponse.error(e.getMessage()))));
    }

    @PostMapping("/test-key")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> testProviderKey(@RequestBody Map<String, String> payload) {
        String name = payload.get("name");
        String apiKey = payload.get("apiKey");

        if (name == null || apiKey == null) {
            return Mono.just(ResponseEntity.badRequest().body(ApiResponse.error("name and apiKey are required")));
        }

        return providerAdminService.validateKey(name, apiKey)
                .map(valid -> {
                    if (valid) {
                        return ResponseEntity.ok(ApiResponse.ok(Map.of("message", "Key validated successfully", "valid", true)));
                    } else {
                        return ResponseEntity.status(401).body(ApiResponse.error("Invalid key or provider error"));
                    }
                });
    }

    @GetMapping("/discover")
    public Mono<ResponseEntity<ApiResponse<List<Map<String, Object>>>>> discoverModels(@RequestParam(required = false) String query) {
        return discoveryService.discoverModels(query)
                .collectList()
                .map(list -> ResponseEntity.ok(ApiResponse.ok(list)));
    }

    @GetMapping("/scan")
    public Mono<ResponseEntity<ApiResponse<List<Map<String, Object>>>>> scanDeployments() {
        return discoveryService.scanDeployments()
                .collectList()
                .map(list -> ResponseEntity.ok(ApiResponse.ok(list)));
    }

    @GetMapping("/{id}/suggest-roles")
    public Mono<ResponseEntity<ApiResponse<List<String>>>> suggestRoles(@PathVariable String id) {
        return providerAdminService.getAllProviders()
                .filter(p -> p.getId().equals(id))
                .next()
                .map(provider -> ResponseEntity.ok(ApiResponse.ok(providerAdminService.suggestRoles(provider))))
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.error("Provider not found")));
    }

    @PatchMapping("/{id}/capability")
    public Mono<ResponseEntity<ApiResponse<APIProvider>>> patchCapability(
            @PathVariable String id, 
            @RequestBody Map<String, Object> updates) {
        return getCurrentAdminUserId()
                .flatMap(adminUserId -> providerAdminService.patchCapability(id, updates, adminUserId))
                .map(saved -> ResponseEntity.ok(ApiResponse.ok(saved)))
                .defaultIfEmpty(ResponseEntity.status(404).body(ApiResponse.error("Provider not found")));
    }

    @PostMapping("/test-all")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> testAllProviders() {
        providerAdminService.triggerValidation();
        return Mono.just(ResponseEntity.ok(ApiResponse.ok(Map.of(
            "status", "validation_started",
            "message", "সিস্টেম সব কী চেক করা শুরু করেছে। কিছুক্ষণের মধ্যে রিপোর্ট আপডেট হবে।"
        ))));
    }

    @GetMapping("/health-stats")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> getHealthStats() {
        return providerAdminService.getHealthStats()
                .map(stats -> ResponseEntity.ok(ApiResponse.ok(stats)));
    }

    @DeleteMapping("/bulk-remove-dead")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> removeDeadProviders() {
        return getCurrentAdminUserId()
                .flatMap(adminUserId -> providerAdminService.removeDeadProviders(adminUserId))
                .then(Mono.just(ResponseEntity.ok(ApiResponse.ok(Map.of(
                    "message", "সব ডেড কী সফলভাবে রিমুভ করা হয়েছে।"
                )))));
    }
}
