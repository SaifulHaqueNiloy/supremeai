package com.supremeai.service;

import com.supremeai.model.SystemConfig;
import com.supremeai.repository.SystemConfigRepository;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * SystemConfigSeeder — seeds default system configuration into Firestore on first startup.
 *
 * Seeds the "system_configs" collection with document id "global_settings".
 * Uses idempotent check: only writes if document does not already exist.
 *
 * Configuration seeded:
 * - Tier quotas (GUEST/FREE/BASIC/PRO/ENTERPRISE/ADMIN)
 * - Max API keys per tier
 * - Simulator install limits per tier
 * - Default AI model settings
 * - Permission defaults
 * - Lifecycle & learning defaults (stored as provider config map)
 */
@Component
public class SystemConfigSeeder {

    private static final Logger log = LoggerFactory.getLogger(SystemConfigSeeder.class);

    @Autowired
    private SystemConfigRepository systemConfigRepository;

    @PostConstruct
    public void seedSystemConfig() {
        systemConfigRepository.findById("global_settings")
            .hasElement()
            .flatMap(exists -> {
                if (!exists) {
                    log.info("[CONFIG_SEED] No global_settings found — seeding default system config...");
                    return systemConfigRepository.save(buildDefaultConfig());
                } else {
                    log.info("[CONFIG_SEED] global_settings already exists — skipping seed");
                    return reactor.core.publisher.Mono.empty();
                }
            })
            .subscribe(
                config -> log.info("[CONFIG_SEED] Default system config seeded successfully"),
                error -> log.error("[CONFIG_SEED] Failed to seed system config: {}", error.getMessage())
            );
    }

    private SystemConfig buildDefaultConfig() {
        SystemConfig config = new SystemConfig();
        config.setId("global_settings");

        // Active AI models (primary + fallback)
        config.setActiveModel("google/gemini-1.5-flash");
        config.setSmallModel("google/gemini-1.5-flash");
        config.setVersion(1L);

        // Operational flags
        config.setMaintenanceMode(false);
        config.setEmergencyStop(false);
        config.setApiAccessLock(false);
        config.setApiRotationStrategy("quota-based");
        config.setAutoExecApprovalRequired(true);
        config.setFullAuthority(false);
        config.setShareMode("manual");
        config.setEnableExternalDirectory(false);
        config.setEmailNotifications(true);
        config.setSmsAlerts(false);

        // System message / AI persona
        config.setSystemMessage(
            "You are SupremeAI, an expert software architect and full-stack developer. " +
            "You help users build, deploy, and manage AI-powered applications. " +
            "You are precise, helpful, and always explain your reasoning. " +
            "Default language: English. Switch to Bengali (বাংলা) if user speaks Bengali."
        );

        // Permission defaults
        config.setPermissions(Map.of(
            "read", "allow",
            "edit", "ask",
            "bash", "ask",
            "task", "allow",
            "websearch", "allow",
            "external_directory", "deny",
            "file_delete", "ask",
            "git_push", "ask",
            "deploy", "ask"
        ));

        // AI provider configurations (GCP Deployed Landscape)
        config.setProviders(Map.of(
            "gemini", Map.of(
                "enabled", true,
                "model", "gemini-1.5-flash",
                "description", "Primary Orchestrator & Multimodal Specialist (1M Context)",
                "maxTokens", 1000000,
                "rotationThreshold", 0.85,
                "priority", 1
            ),
            "openai", Map.of(
                "enabled", true,
                "model", "gpt-4o-mini",
                "description", "Structured Data & Logic Verification",
                "maxTokens", 128000,
                "rotationThreshold", 0.80,
                "priority", 2
            ),
            "anthropic", Map.of(
                "enabled", true,
                "model", "claude-3-haiku-20240307",
                "description", "Safety Monitoring & Refined Communication",
                "maxTokens", 200000,
                "rotationThreshold", 0.80,
                "priority", 3
            ),
            "vertex_llama", Map.of(
                "enabled", true,
                "model", "llama-3.1",
                "description", "Llama 3.1 - State-of-the-art open model (Low Latency)",
                "maxTokens", 128000,
                "rotationThreshold", 0.70,
                "priority", 4
            ),
            "deepseek", Map.of(
                "enabled", true,
                "model", "deepseek-v4pro",
                "description", "Advanced Coding & Technical Architect (GCloud Pro)",
                "maxTokens", 64000,
                "rotationThreshold", 0.80,
                "priority", 5
            )
        ));

        log.debug("[CONFIG_SEED] Built default config: model={} maintenance={}",
            config.getActiveModel(), config.isMaintenanceMode());

        return config;
    }
}
