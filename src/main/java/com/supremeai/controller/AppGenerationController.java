package com.supremeai.controller;

import com.supremeai.service.CodeGenerationService;
import com.supremeai.generation.FullStackCodeGenerator;
import com.supremeai.generation.MultiPlatformGenerator;
import com.supremeai.model.GeneratedApp;
import com.supremeai.model.EntityDefinition;
import com.supremeai.model.FieldDefinition;
import com.supremeai.repository.GeneratedAppRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import com.supremeai.dto.AppGenerationRequest;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;
import com.supremeai.response.ApiResponse;
import java.util.UUID;

/**
 * Controller for app generation endpoints.
 * Handles requests to generate applications based on user requirements.
 */
@RestController
@RequestMapping({"/api/generate", "/api/teaching/create-app"})
public class AppGenerationController {
    
    private static final Logger logger = LoggerFactory.getLogger(AppGenerationController.class);
    
    @Autowired
    private CodeGenerationService codeGenerationService;
    
    @Autowired
    private FullStackCodeGenerator fullStackCodeGenerator;
    
    @Autowired
    private MultiPlatformGenerator multiPlatformGenerator;

    @Autowired
    private GeneratedAppRepository generatedAppRepository;

    @PostMapping
    @PreAuthorize("hasAnyRole('USER', 'ADMIN', 'GUEST')")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> generateApp(
            @Valid @RequestBody AppGenerationRequest request,
            Authentication auth) {
        return Mono.fromCallable(() -> {
            String name = request.getName();
            String description = request.getDescription();
            String platform = request.getPlatform();
            String database = request.getDatabase();
            String type = request.getType();
            boolean useAI = request.isUseAI();

            String userId = auth != null ? auth.getName() : "anonymous";

            logger.info("Generating app: {} (platform: {}, database: {}, AI: {}) by user {}", name, platform, database, useAI, userId);
            
            Map<String, String> decisions = new HashMap<>();
            decisions.put("architecture", "monolith");
            decisions.put("database", database);
            decisions.put("apiStyle", "REST");
            decisions.put("authType", "JWT");
            decisions.put("frontend", "React");
            decisions.put("deployment", "GCP");
            
            Map<String, Object> result;
            
            // Use enhanced AI-powered generation if requested
            if (useAI) {
                List<EntityDefinition> entities = request.getEntities();
                if (entities == null) entities = new ArrayList<>();
                result = codeGenerationService.generateAppWithAI(
                    name, description, entities, database, "JWT"
                );
            } else {
                // Use appropriate generator based on platform
                switch (platform.toLowerCase()) {
                    case "fullstack":
                        result = codeGenerationService.generateFromContext(decisions);
                        break;
                        
                    case "web":
                    case "android":
                    case "ios":
                    case "desktop":
                        Map<String, String> platformResult = multiPlatformGenerator.generateForPlatform(
                            description != null && !description.isEmpty() ? description : name, 
                            platform
                        );
                        result = new HashMap<>(platformResult);
                        result.put("decisions", decisions);
                        break;
                        
                    default:
                        // Default to fullstack generation
                        result = codeGenerationService.generateFromContext(decisions);
                        break;
                }
            }
            
            // Add metadata
            result.put("name", name);
            result.put("description", description);
            result.put("platform", platform);
            result.put("type", type);
            result.put("status", "GENERATED");
            result.put("message", "App generated successfully");

            // Persist generated app to Firestore for simulator preview
            String appId = UUID.randomUUID().toString();
            GeneratedApp generatedApp = new GeneratedApp(appId, userId, platform, "React");
            // For now, store placeholder HTML; will be replaced with actual build output
            String placeholderHtml = String.format(
                "<!DOCTYPE html><html><head><title>%s</title><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"></head>" +
                "<body style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#f5f5f5\">" +
                "<div style=\"text-align:center;padding:40px;background:white;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1)\">" +
                "<h1 style=\"color:#333\">%s</h1>" +
                "<p style=\"color:#666\">Your generated app is being built.</p>" +
                "<p style=\"color:#999;font-size:12px\">Simulator preview will be available shortly.</p>" +
                "<p><small>App ID: %s</small></p>" +
                "</div></body></html>",
                name, name, appId
            );
            generatedApp.setHtmlContent(placeholderHtml);
            generatedApp.setVersion("1.0.0");
            generatedApp.setStatus("GENERATED");
            generatedAppRepository.save(generatedApp).subscribe();

            result.put("appId", appId);

            logger.info("App generation completed: {} ({} files) appId={}", name, result.getOrDefault("fileCount", 0), appId);
            
            return ResponseEntity.ok(ApiResponse.ok(result));
        }).subscribeOn(Schedulers.boundedElastic())
        .onErrorResume(e -> {
            logger.error("App generation failed", e);
            return Mono.just(ResponseEntity.internalServerError().body(ApiResponse.error("App generation failed: " + e.getMessage())));
        });
    }
    
    /**
     * Parse entity definitions from request
     */
    @SuppressWarnings("unchecked")
    private List<EntityDefinition> parseEntitiesFromRequest(Map<String, Object> request) {
        List<EntityDefinition> entities = new ArrayList<>();
        
        // Check if custom entities are provided
        if (request.containsKey("entities")) {
            List<Map<String, Object>> entityMaps = (List<Map<String, Object>>) request.get("entities");
            for (Map<String, Object> entityMap : entityMaps) {
                EntityDefinition entity = new EntityDefinition();
                entity.setName((String) entityMap.get("name"));
                entity.setDescription((String) entityMap.get("description"));
                
                List<FieldDefinition> fields = new ArrayList<>();
                if (entityMap.containsKey("fields")) {
                    List<Map<String, Object>> fieldMaps = (List<Map<String, Object>>) entityMap.get("fields");
                    for (Map<String, Object> fieldMap : fieldMaps) {
                        FieldDefinition field = new FieldDefinition();
                        field.setName((String) fieldMap.get("name"));
                        field.setType((String) fieldMap.get("type"));
                        field.setRequired((Boolean) fieldMap.getOrDefault("required", false));
                        field.setUnique((Boolean) fieldMap.getOrDefault("unique", false));
                        if (fieldMap.containsKey("maxLength")) {
                            field.setMaxLength(((Number) fieldMap.get("maxLength")).intValue());
                        }
                        fields.add(field);
                    }
                }
                entity.setFields(fields);
                entities.add(entity);
            }
        } else {
            // Default to Product entity
            entities.add(createDefaultProductEntity());
        }
        
        return entities;
    }
    
    /**
     * Create default Product entity
     */
    private EntityDefinition createDefaultProductEntity() {
        EntityDefinition entity = new EntityDefinition();
        entity.setName("Product");
        entity.setDescription("Product entity with basic fields");
        
        List<FieldDefinition> fields = new ArrayList<>();
        
        FieldDefinition nameField = new FieldDefinition();
        nameField.setName("name");
        nameField.setType("string");
        nameField.setRequired(true);
        nameField.setMaxLength(255);
        fields.add(nameField);
        
        FieldDefinition descField = new FieldDefinition();
        descField.setName("description");
        descField.setType("text");
        descField.setRequired(false);
        fields.add(descField);
        
        FieldDefinition priceField = new FieldDefinition();
        priceField.setName("price");
        priceField.setType("double");
        priceField.setRequired(true);
        fields.add(priceField);
        
        FieldDefinition stockField = new FieldDefinition();
        stockField.setName("stock");
        stockField.setType("integer");
        stockField.setRequired(false);
        fields.add(stockField);
        
        FieldDefinition categoryField = new FieldDefinition();
        categoryField.setName("category");
        categoryField.setType("string");
        categoryField.setRequired(false);
        categoryField.setMaxLength(100);
        fields.add(categoryField);
        
        entity.setFields(fields);
        return entity;
    }
    
    /**
     * Health check endpoint.
     */
    @GetMapping("/health")
    public Mono<ResponseEntity<ApiResponse<Map<String, String>>>> health() {
        Map<String, String> health = new HashMap<>();
        health.put("status", "UP");
        health.put("service", "AppGenerationService");
        return Mono.just(ResponseEntity.ok(ApiResponse.ok(health)));
    }
    
    /**
     * Preview generation - returns sample output without creating files.
     */
    @PostMapping("/preview")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> previewGeneration(@RequestBody Map<String, Object> request) {
        return Mono.fromCallable(() -> {
            String platform = (String) request.getOrDefault("platform", "fullstack");
            
            Map<String, String> decisions = new HashMap<>();
            decisions.put("architecture", "monolith");
            decisions.put("database", "PostgreSQL");
            decisions.put("apiStyle", "REST");
            decisions.put("authType", "JWT");
            decisions.put("frontend", "React");
            decisions.put("deployment", "GCP");
            
            Map<String, Object> result = codeGenerationService.generateFromContext(decisions);
            
            // Limit preview to first few files
            @SuppressWarnings("unchecked")
            Map<String, String> files = (Map<String, String>) result.get("files");
            if (files != null && files.size() > 3) {
                Map<String, String> previewFiles = new HashMap<>();
                int count = 0;
                for (Map.Entry<String, String> entry : files.entrySet()) {
                    if (count++ >= 3) break;
                    previewFiles.put(entry.getKey(), entry.getValue());
                }
                result.put("files", previewFiles);
                result.put("preview", true);
                result.put("totalFiles", files.size());
            }
            
            return ResponseEntity.ok(ApiResponse.ok(result));
            
        }).subscribeOn(Schedulers.boundedElastic())
        .onErrorResume(e -> {
            logger.error("Preview generation failed", e);
            return Mono.just(ResponseEntity.internalServerError().body(ApiResponse.error("Preview generation failed: " + e.getMessage())));
        });
    }
}
