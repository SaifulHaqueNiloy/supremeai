package com.supremeai.service;

import com.supremeai.model.SystemConfig;
import com.supremeai.repository.SystemConfigRepository;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Map;
import reactor.core.publisher.Mono;

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
                    return Mono.empty();
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

        // AI provider configurations (Comprehensive All-in-One Landscape)
        config.setProviders(Map.ofEntries(
            Map.entry("gemini", Map.of(
                "enabled", true,
                "model", "gemini-1.5-flash",
                "description", "Primary Orchestrator & Multimodal Specialist (1M Context)",
                "maxTokens", 1000000,
                "rotationThreshold", 0.85,
                "priority", 1
            )),
            Map.entry("hf_codellama", Map.of(
                "enabled", true,
                "model", "CodeLlama-34b-Instruct-hf",
                "description", "HF - Primary Code Generation (Serverless)",
                "maxTokens", 16000,
                "rotationThreshold", 0.80,
                "priority", 2
            )),
            Map.entry("hf_mistral", Map.of(
                "enabled", true,
                "model", "Mistral-7B-Instruct-v0.3",
                "description", "HF - Major Chat & Conversation (Instruct)",
                "maxTokens", 32000,
                "rotationThreshold", 0.80,
                "priority", 3
            )),
            Map.entry("hf_llama3", Map.of(
                "enabled", true,
                "model", "Meta-Llama-3-8B-Instruct",
                "description", "HF - Google Alternative / Bengali Support",
                "maxTokens", 8192,
                "rotationThreshold", 0.70,
                "priority", 4
            )),
            Map.entry("hf_phi_vision", Map.of(
                "enabled", true,
                "model", "Phi-3-vision-128k-instruct",
                "description", "HF - Specialized Vision & Image Analysis",
                "maxTokens", 128000,
                "rotationThreshold", 0.80,
                "priority", 5
            )),
            Map.entry("hf_e5_large", Map.of(
                "enabled", true,
                "model", "multilingual-e5-large",
                "description", "HF - Multilingual Embeddings for RAG",
                "maxTokens", 512,
                "rotationThreshold", 0.90,
                "priority", 6
            )),
            Map.entry("render_phi2", Map.of(
                "enabled", true,
                "model", "phi-2",
                "description", "Render - Fast Response / Free Tier Docker",
                "maxTokens", 2048,
                "rotationThreshold", 0.60,
                "priority", 7
            )),
            Map.entry("render_tinyllama", Map.of(
                "enabled", true,
                "model", "tinyllama-1.1b",
                "description", "Render - Emergency Fallback (Always Free)",
                "maxTokens", 1024,
                "rotationThreshold", 0.50,
                "priority", 8
            )),
            Map.entry("render_phi3", Map.of(
                "enabled", true,
                "model", "phi-3-mini",
                "description", "Render - Balanced Quality (Docker)",
                "maxTokens", 4096,
                "rotationThreshold", 0.70,
                "priority", 9
            )),
            Map.entry("render_qwen", Map.of(
                "enabled", true,
                "model", "qwen-0.5b",
                "description", "Render - Ultra-Lightweight (Best for Free Tier)",
                "maxTokens", 2048,
                "rotationThreshold", 0.40,
                "priority", 10
            )),
            Map.entry("openai", Map.of(
                "enabled", true,
                "model", "gpt-4o-mini",
                "description", "Backup - Structured Data & Logic Verification",
                "maxTokens", 128000,
                "rotationThreshold", 0.80,
                "priority", 11
            )),
            Map.entry("deepseek", Map.of(
                "enabled", true,
                "model", "deepseek-v4pro",
                "description", "Professional Coding & Technical Architect",
                "maxTokens", 64000,
                "rotationThreshold", 0.80,
                "priority", 12
            ))
        ));

        log.debug("[CONFIG_SEED] Built default config: model={} maintenance={}",
            config.getActiveModel(), config.isMaintenanceMode());

        return config;
    }
}
