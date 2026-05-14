package com.supremeai.service;

import com.supremeai.model.EntityDefinition;
import com.supremeai.model.ReverseEngineeringJob;
import com.supremeai.repository.ReverseEngineeringJobRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import org.springframework.security.access.prepost.PreAuthorize;
import java.util.HashMap;
import java.util.UUID;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Bridges completed reverse engineering jobs to code generation.
 * When a reverse engineering job finishes, this service can automatically
 * generate an application that integrates with the discovered APIs.
 */
@Service
public class ReverseEngineeringIntegrationService {

    private static final Logger logger = LoggerFactory.getLogger(ReverseEngineeringIntegrationService.class);

    @Autowired
    private ReverseEngineeringJobRepository jobRepository;

    @Autowired
    private CodeGenerationService codeGenerationService;

    @Autowired
    private PubSubPublisherService pubSubPublisherService;

    @Autowired
    private SimulatorService simulatorService;

    private static final String PUBSUB_TOPIC = "reverse-engineering-jobs";

    /**
     * Called when a reverse engineering job completes.
     * Generates an app that uses the discovered APIs and optionally deploys to simulator.
     */
    @PreAuthorize("hasRole('ADMIN')")
    public Mono<ReverseEngineeringJob> onJobCompletion(String jobId, String userId) {
        logger.info("[ReverseEngIntegration] Processing completed job: {}", jobId);

        return jobRepository.findByJobId(jobId)
            .flatMap(job -> {
                if (!job.getUserId().equals(userId)) {
                    return Mono.error(new RuntimeException("Unauthorized: job does not belong to user"));
                }
                if (!"COMPLETED".equals(job.getStatus())) {
                    return Mono.error(new RuntimeException("Job not completed: " + job.getStatus()));
                }

                // Build requirements from discovered APIs
                String requirements = buildRequirementsFromJob(job);
                Map<String, Object> apis = job.getDiscoveredApis();

                // Prepare entities from API endpoints
                List<EntityDefinition> entities = extractEntitiesFromApis(apis);

                // Trigger code generation with AI
                Map<String, Object> result = codeGenerationService.generateAppWithAI(
                    "API Integration: " + job.getWebsiteUrl(),
                    requirements,
                    entities,
                    "PostgreSQL",
                    "JWT"
                );

                String appId = (String) result.get("appId");
                job.setGeneratedAppId(appId);
                job.setStatus("INTEGRATED");

                return jobRepository.save(job)
                    .map(savedJob -> {
                        logger.info("[ReverseEngIntegration] Generated app: {} from job {}", appId, jobId);
                        return savedJob;
                    });
            });
    }

    private String buildRequirementsFromJob(ReverseEngineeringJob job) {
        Map<String, Object> apis = job.getDiscoveredApis();
        if (apis != null && !apis.isEmpty()) {
            return String.format(
                "Build an application that integrates with APIs discovered from website %s. " +
                "Discovered %d endpoints. Include authentication handling, API service layer, and example UI screens.",
                job.getWebsiteUrl(),
                apis.size()
            );
        }
        return String.format(
            "Create an application that scrapes and displays data from %s.",
            job.getWebsiteUrl()
        );
    }

    private List<EntityDefinition> extractEntitiesFromApis(Map<String, Object> apis) {
        // Convert API endpoints to entity definitions
        // Stub: in production, analyze endpoint paths and data structures
        return List.of();
    }

    /**
     * In production, this would be invoked via Pub/Sub or HTTP webhook.
     */
    @PreAuthorize("hasRole('ADMIN')")
    public Mono<ReverseEngineeringJob> startJob(String userId, String websiteUrl, String taskType, String customInstructions, Map<String, Object> extraParams) {
        String jobId = "reveng_" + UUID.randomUUID().toString().substring(0, 12);
        ReverseEngineeringJob job = new ReverseEngineeringJob(jobId, userId, websiteUrl, taskType);
        job.setCustomInstructions(customInstructions);
        job.setStatus("PENDING");
        
        return jobRepository.save(job)
            .doOnNext(saved -> {
                logger.info("[ReverseEngIntegration] Job created: {} for {} (Type: {})", jobId, websiteUrl, taskType);
                
                // Publish to Pub/Sub
                Map<String, Object> message = new HashMap<>();
                message.put("jobId", jobId);
                message.put("userId", userId);
                message.put("websiteUrl", websiteUrl);
                message.put("taskType", taskType);
                message.put("customInstructions", customInstructions);
                
                if (extraParams != null) {
                    message.putAll(extraParams);
                }
                
                try {
                    pubSubPublisherService.publish(PUBSUB_TOPIC, message);
                    logger.info("[ReverseEngIntegration] Published job {} to topic {}", jobId, PUBSUB_TOPIC);
                } catch (Exception e) {
                    logger.error("[ReverseEngIntegration] Failed to publish to Pub/Sub: {}", e.getMessage());
                }
            });
    }

    /**
     * Simulate job completion (for testing). In production, Python FastAPI worker calls this.
     */
    public Mono<ReverseEngineeringJob> completeJob(String jobId, Map<String, Object> discoveredApis) {
        return jobRepository.findByJobId(jobId)
            .flatMap(job -> {
                job.setStatus("COMPLETED");
                job.setDiscoveredApis(discoveredApis);
                return jobRepository.save(job);
            })
            .doOnNext(job -> logger.info("[ReverseEngIntegration] Job marked completed: {}", jobId));
    }

    /**
     * Fetch recent reverse engineering jobs (for admin history).
     * Fetches all, sorts by createdAt descending, limits to N.
     */
    @PreAuthorize("hasRole('ADMIN')")
    public Mono<List<ReverseEngineeringJob>> getRecentJobs(int limit) {
        return jobRepository.findAll()
            .collectList()
            .map(list -> list.stream()
                .sorted((j1, j2) -> {
                    if (j1.getCreatedAt() == null && j2.getCreatedAt() == null) return 0;
                    if (j1.getCreatedAt() == null) return 1;
                    if (j2.getCreatedAt() == null) return -1;
                    return j2.getCreatedAt().compareTo(j1.getCreatedAt());
                })
                .limit(limit)
                .collect(Collectors.toList())
            );
    }
}
