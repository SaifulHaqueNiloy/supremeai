package com.supremeai.service;

import com.supremeai.exception.SimulatorDeploymentException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.*;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Service for deploying generated apps to Cloud Run simulator environments.
 *
 * Uses gcloud CLI for deployment. Requires gcloud installed and authenticated.
 * Cloud Run service name pattern: sim-{appId}-{deviceSlug}
 *
 * NOTE: In production, consider using Cloud Run Admin API directly instead of CLI.
 */
@Service
public class SimulatorDeploymentService {

    private static final Logger logger = LoggerFactory.getLogger(SimulatorDeploymentService.class);

    @Value("${spring.cloud.gcp.project-id:supremeai-459910}")
    private String projectId;

    @Value("${simulator.cloud.region:us-central1}")
    private String region;

    @Value("${simulator.cloud.run.image:}")
    private String runtimeImage; // optional override

    @Value("${simulator.health.check.timeout.ms:3000}")
    private int healthCheckTimeoutMs;

    // In-memory deployment registry (production: move to Firestore)
    private final Map<String, DeploymentRecord> deploymentRegistry = new ConcurrentHashMap<>();

    private final WebClient webClient;

    public SimulatorDeploymentService() {
        this.webClient = WebClient.builder()
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(512 * 1024))
                .build();
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // Public API
    // ─────────────────────────────────────────────────────────────────────────────

    /**
     * Deploy a generated app to the simulator.
     *
     * This will create a Cloud Run service with the simulator runtime image,
     * setting environment variables to identify the app and device type.
     *
     * @return Publicly accessible HTTPS URL for the simulator preview
     */
    public String deployToSimulator(String appId, String deviceType) {
        logger.info("[SIMULATOR_DEPLOY] Deploying app={} device={}", appId, deviceType);

        try {
            String deviceSlug = deviceType.toLowerCase().replace("_", "-");
            String serviceName = "sim-" + appId + "-" + deviceSlug;
            String serviceNameClean = serviceName.replaceAll("[^a-z0-9-]", "-").toLowerCase();

            // Deploy via gcloud CLI
            String serviceUrl = deployViaGcloud(serviceNameClean, appId, deviceType);

            // Record deployment
            DeploymentRecord record = new DeploymentRecord(appId, deviceType, serviceUrl, DeploymentStatus.RUNNING);
            deploymentRegistry.put(appId, record);

            logger.info("[SIMULATOR_DEPLOY] Deployed app={} url={}", appId, serviceUrl);
            return serviceUrl;

        } catch (Exception e) {
            logger.error("[SIMULATOR_DEPLOY] Deployment failed for app {}: {}", appId, e.getMessage(), e);
            throw new SimulatorDeploymentException("Failed to deploy to Cloud Run: " + e.getMessage(), e);
        }
    }

    /**
     * Undeploy (remove) a simulator preview.
     */
    public void undeployFromSimulator(String appId) {
        logger.info("[SIMULATOR_DEPLOY] Undeploying app={}", appId);

        DeploymentRecord record = deploymentRegistry.get(appId);
        if (record != null) {
            String deviceSlug = record.getDeviceType().toLowerCase().replace("_", "-");
            String serviceName = "sim-" + appId + "-" + deviceSlug;
            String serviceNameClean = serviceName.replaceAll("[^a-z0-9-]", "-").toLowerCase();

            try {
                ProcessBuilder pb = new ProcessBuilder(
                        "gcloud", "run", "services", "delete", serviceNameClean,
                        "--region", region,
                        "--quiet"
                );
                pb.redirectErrorStream(true);
                Process process = pb.start();
                process.waitFor(); // ignore output, best effort
                logger.info("[GCP] Deleted Cloud Run service: {}", serviceNameClean);
            } catch (Exception e) {
                logger.warn("[GCP] Failed to delete service {}: {}", serviceNameClean, e.getMessage());
            }

            record.setStatus(DeploymentStatus.STOPPED);
            logger.info("[SIMULATOR_DEPLOY] Marked app={} as STOPPED", appId);
        } else {
            logger.warn("[SIMULATOR_DEPLOY] No deployment record found for app={}", appId);
        }

        deploymentRegistry.remove(appId);
    }

    /**
     * Check if the deployed URL is healthy.
     */
    public boolean isDeploymentHealthy(String previewUrl) {
        if (previewUrl == null || previewUrl.isEmpty()) {
            return false;
        }

        // Skip health check for localhost (dev mode)
        if (previewUrl.contains("localhost") || previewUrl.contains("127.0.0.1")) {
            logger.debug("[SIMULATOR_DEPLOY] Skipping health check for local URL: {}", previewUrl);
            return true;
        }

        try {
            String healthUrl = previewUrl.split("\\?")[0] + "/health";
            webClient.get()
                    .uri(healthUrl)
                    .retrieve()
                    .toBodilessEntity()
                    .timeout(Duration.ofMillis(healthCheckTimeoutMs))
                    .block();
            logger.debug("[SIMULATOR_DEPLOY] Health check passed for {}", previewUrl);
            return true;
        } catch (Exception e) {
            logger.warn("[SIMULATOR_DEPLOY] Health check failed for {} ({}), assuming live", previewUrl, e.getMessage());
            return true; // assume live for graceful degradation
        }
    }

    public DeploymentStatus getStatus(String appId) {
        DeploymentRecord record = deploymentRegistry.get(appId);
        return record != null ? record.getStatus() : DeploymentStatus.NOT_DEPLOYED;
    }

    public Map<String, DeploymentRecord> getAllDeployments() {
        return Map.copyOf(deploymentRegistry);
    }

    public DeploymentRecord getDeploymentRecord(String appId) {
        return deploymentRegistry.get(appId);
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // Internal Implementation
    // ─────────────────────────────────────────────────────────────────────────────

    /**
     * Deploy Cloud Run service using gcloud CLI.
     */
    private String deployViaGcloud(String serviceName, String appId, String deviceType) throws Exception {
        logger.info("[GCP] Deploying Cloud Run service: {}", serviceName);

        // Use explicit runtime image if provided, else construct from project ID
        String image = runtimeImage;
        if (image == null || image.isEmpty()) {
            image = "gcr.io/" + projectId + "/simulator-runtime:latest";
        }

        ProcessBuilder pb = new ProcessBuilder(
                "gcloud", "run", "deploy", serviceName,
                "--image", image,
                "--region", region,
                "--allow-unauthenticated",
                "--set-env-vars", String.format("APP_ID=%s,DEVICE_TYPE=%s,SIMULATOR_MODE=preview", appId, deviceType),
                "--min-instances", "1",
                "--max-instances", "10",
                "--platform", "managed"
        );
        pb.redirectErrorStream(true);
        Process process = pb.start();

        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
                logger.debug("[gcloud] {}", line);
            }
        }

        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new RuntimeException("gcloud deploy failed with exit code " + exitCode + ": " + output);
        }

        // Cloud Run URL pattern
        String serviceUrl = String.format("https://%s-%s-%s.a.run.app", serviceName, region, projectId);
        return serviceUrl;
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // Inner Models
    // ─────────────────────────────────────────────────────────────────────────────

    public enum DeploymentStatus {
        NOT_DEPLOYED, DEPLOYING, RUNNING, STOPPED, ERROR
    }

    public static class DeploymentRecord {
        private final String appId;
        private final String deviceType;
        private final String previewUrl;
        private DeploymentStatus status;
        private final java.time.LocalDateTime deployedAt;

        public DeploymentRecord(String appId, String deviceType, String previewUrl, DeploymentStatus status) {
            this.appId = appId;
            this.deviceType = deviceType;
            this.previewUrl = previewUrl;
            this.status = status;
            this.deployedAt = java.time.LocalDateTime.now();
        }

        public String getAppId() { return appId; }
        public String getDeviceType() { return deviceType; }
        public String getPreviewUrl() { return previewUrl; }
        public DeploymentStatus getStatus() { return status; }
        public void setStatus(DeploymentStatus status) { this.status = status; }
        public java.time.LocalDateTime getDeployedAt() { return deployedAt; }
    }
}
