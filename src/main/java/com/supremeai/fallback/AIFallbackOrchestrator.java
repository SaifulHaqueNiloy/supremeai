package com.supremeai.fallback;

import com.supremeai.cost.QuotaManager;
import com.supremeai.learning.knowledge.GlobalKnowledgeBase;
import com.supremeai.learning.immunity.CodeImmunitySystem;
import com.supremeai.intelligence.profiling.AIProfiler;
import com.supremeai.provider.AIProviderType;
import com.supremeai.provider.AIProviderFactory;
import com.supremeai.resilience.RetryableAIExecutor;
import com.supremeai.security.ApiKeyRotationService;
import com.supremeai.model.UserApiKey;
import com.supremeai.service.EnhancedLearningService;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import javax.annotation.PostConstruct;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class AIFallbackOrchestrator {

    private static final Logger log = LoggerFactory.getLogger(AIFallbackOrchestrator.class);
    private final QuotaManager quotaManager;
    private final GlobalKnowledgeBase knowledgeBase;
    private final CodeImmunitySystem immunitySystem;
    private final AIProfiler aiProfiler;
    private final RetryableAIExecutor retryExecutor;
    private final ApiKeyRotationService keyRotationService;
    private final AIProviderFactory providerFactory;

    @Autowired(required = false)
    private EnhancedLearningService enhancedLearningService;

    private final CircuitBreakerRegistry circuitBreakerRegistry;
    private final Map<AIProviderType, CircuitBreaker> providerCircuitBreakers = new EnumMap<>(AIProviderType.class);
    private final com.supremeai.repository.ProviderRepository providerRepository;

    private final List<AIProviderType> allProviders = Arrays.asList(
            // Tier 1: High Performance External
            AIProviderType.GROQ_LLAMA3,
            AIProviderType.GEMINI_PRO,
            AIProviderType.ANTHROPIC_CLAUDE,
            AIProviderType.OPENAI,
            AIProviderType.DEEPSEEK,
            
            // Tier 2: Resilient Private Cloud
            AIProviderType.CLOUD_QWEN,
            AIProviderType.CLOUD_DEEPSEEK,
            AIProviderType.CLOUD_LLAMA,
            AIProviderType.CLOUD_PHI,
            
            // Other External
            AIProviderType.HUGGINGFACE_FREE,
            AIProviderType.KIMI,
            AIProviderType.MISTRAL,
            AIProviderType.STEPFUN,
            
            // Tier 3: Last Resort Local
            AIProviderType.OLLAMA
    );

    public AIFallbackOrchestrator(QuotaManager quotaManager,
                                  GlobalKnowledgeBase knowledgeBase, CodeImmunitySystem immunitySystem,
                                  AIProfiler aiProfiler, RetryableAIExecutor retryExecutor,
                                  ApiKeyRotationService keyRotationService,
                                  AIProviderFactory providerFactory,
                                  com.supremeai.repository.ProviderRepository providerRepository) {
        this.providerRepository = providerRepository;
        this.quotaManager = quotaManager;
        this.knowledgeBase = knowledgeBase;
        this.immunitySystem = immunitySystem;
        this.aiProfiler = aiProfiler;
        this.retryExecutor = retryExecutor;
        this.keyRotationService = keyRotationService;
        this.providerFactory = providerFactory;

        CircuitBreakerConfig config = CircuitBreakerConfig.custom()
                .failureRateThreshold(50)
                .waitDurationInOpenState(Duration.ofSeconds(30))
                .slidingWindowSize(10)
                .permittedNumberOfCallsInHalfOpenState(3)
                .build();

        this.circuitBreakerRegistry = CircuitBreakerRegistry.of(config);
    }

    @PostConstruct
    public void init() {
        for (AIProviderType provider : allProviders) {
            getOrCreateCircuitBreaker(provider.name().toLowerCase());
        }
    }

    private CircuitBreaker getOrCreateCircuitBreaker(String providerId) {
        String name = providerId.toLowerCase();
        CircuitBreaker cb = circuitBreakerRegistry.find(name).orElseGet(() -> {
            log.info("Creating new dynamic circuit breaker for: {}", name);
            CircuitBreaker newCb = circuitBreakerRegistry.circuitBreaker(name);
            newCb.getEventPublisher()
                    .onStateTransition(event -> log.info("Dynamic Circuit breaker {} transitioned from {} to {}",
                            name, event.getStateTransition().getFromState(), event.getStateTransition().getToState()));
            return newCb;
        });
        return cb;
    }

    public Mono<String> executeWithSupremeIntelligence(String taskCategory, String errorSignature, String prompt) {
        return executeWithSupremeIntelligence(taskCategory, errorSignature, prompt, "system");
    }

    /**
     * Execute with multi-provider fallback, per-provider circuit breakers,
     * retry with backoff, and API key rotation.
     *
     * @param userId Optional user ID for API key selection
     */
    public Mono<String> executeWithSupremeIntelligence(String taskCategory, String errorSignature, String prompt, String userId) {
        // STEP 1: CHECK GLOBAL KNOWLEDGE BASE
        return knowledgeBase.findKnownSolution(errorSignature)
            .switchIfEmpty(Mono.defer(() -> {
                // STEP 2: DYNAMICALLY RE-ORDER THE FALLBACK CHAIN
                AIProviderType expertProvider = aiProfiler.getBestAIForTask(taskCategory);

                return providerRepository.findAll()
                    .filter(p -> "active".equals(p.getStatus()))
                    .filter(p -> {
                        if ("CHAT".equalsIgnoreCase(taskCategory) || "COMMUNICATION".equalsIgnoreCase(taskCategory)) {
                            return p.isCanCommunicate();
                        } else {
                            return p.isCanExecuteTasks();
                        }
                    })
                    .sort(java.util.Comparator.comparingInt(com.supremeai.model.APIProvider::getPriority))
                    .collectList()
                    .onErrorResume(e -> {
                        log.error("Failed to load dynamic providers: {}", e.getMessage());
                        return Mono.just(new ArrayList<com.supremeai.model.APIProvider>());
                    })
                    .flatMap(dbProviders -> {
                        List<Object> dynamicChain = new ArrayList<>();
                        if (expertProvider != null) {
                            dynamicChain.add(expertProvider);
                        }

                        if (dbProviders != null) {
                            for (com.supremeai.model.APIProvider dbp : dbProviders) {
                                boolean existsInChain = false;
                                for (Object o : dynamicChain) {
                                    if (o instanceof AIProviderType && ((AIProviderType) o).name().equalsIgnoreCase(dbp.getType())) {
                                        existsInChain = true; break;
                                    }
                                    if (o instanceof com.supremeai.model.APIProvider && ((com.supremeai.model.APIProvider) o).getName().equalsIgnoreCase(dbp.getName())) {
                                        existsInChain = true; break;
                                    }
                                }
                                if (!existsInChain) {
                                    dynamicChain.add(dbp);
                                }
                            }
                        }

                        for (AIProviderType p : allProviders) {
                            boolean exists = false;
                            for (Object o : dynamicChain) {
                                if (o instanceof AIProviderType && o == p) { exists = true; break; }
                                if (o instanceof String && ((String) o).equalsIgnoreCase(p.name())) { exists = true; break; }
                                if (o instanceof com.supremeai.model.APIProvider && ((com.supremeai.model.APIProvider)o).getType().equalsIgnoreCase(p.name())) { exists = true; break; }
                            }
                            if (!exists) dynamicChain.add(p);
                        }

                        return tryNextProvider(dynamicChain, 0, taskCategory, errorSignature, prompt, userId);
                    });
            }));
    }

    private Mono<String> tryNextProvider(List<Object> chain, int index, String taskCategory, String errorSignature, String prompt, String userId) {
        if (index >= chain.size()) {
            return Mono.error(new RuntimeException("CRITICAL: All AI failed. Cannot execute task."));
        }

        Object pObj = chain.get(index);
        AIProviderType providerType = null;
        com.supremeai.model.APIProvider dbProvider = null;
        String providerId;

        if (pObj instanceof String) {
            providerId = ((String) pObj).toLowerCase();
            try {
                providerType = AIProviderType.valueOf(((String) pObj).toUpperCase());
            } catch (Exception e) { /* Custom provider name */ }
        } else if (pObj instanceof AIProviderType) {
            providerType = (AIProviderType) pObj;
            providerId = providerType.name().toLowerCase();
        } else if (pObj instanceof com.supremeai.model.APIProvider) {
            dbProvider = (com.supremeai.model.APIProvider) pObj;
            providerId = dbProvider.getName().toLowerCase();
        } else {
            return tryNextProvider(chain, index + 1, taskCategory, errorSignature, prompt, userId);
        }

        final AIProviderType finalType = providerType;
        final com.supremeai.model.APIProvider finalDbProvider = dbProvider;
        final String finalProviderId = providerId;
        String serviceName = dbProvider != null ? dbProvider.getType() : getServiceNameForProvider(providerType);

        if (!isServiceQuotaAvailable(serviceName)) {
            log.warn("Quota exhausted for {}, skipping.", serviceName);
            return tryNextProvider(chain, index + 1, taskCategory, errorSignature, prompt, userId);
        }

        CircuitBreaker cb = getOrCreateCircuitBreaker(providerId);
        if (cb.getState() == CircuitBreaker.State.OPEN) {
            log.warn("Circuit breaker OPEN for {}, skipping.", providerId);
            return tryNextProvider(chain, index + 1, taskCategory, errorSignature, prompt, userId);
        }

        long startTime = System.currentTimeMillis();
        log.info("-> Asking {} to handle task: {}", providerId, taskCategory);

        return resolveApiKeyReactive(userId, providerType, dbProvider)
            .flatMap(apiKey -> {
                return Mono.fromCallable(() -> {
                    return retryExecutor.executeWithCircuitBreaker(
                        finalProviderId,
                        finalDbProvider != null ? finalDbProvider.getType() : getServiceNameForProvider(finalType),
                        cb,
                        () -> {
                            try {
                                if (finalDbProvider != null) {
                                    return providerFactory.createProviderFromConfig(finalDbProvider).generate(prompt).block();
                                } else {
                                    return callAIProvider(finalType, apiKey, prompt);
                                }
                            } catch (Exception e) {
                                throw new RuntimeException(e);
                            }
                        }
                    );
                }).subscribeOn(Schedulers.boundedElastic());
            })
            .flatMap(generatedCode -> {
                long timeTaken = System.currentTimeMillis() - startTime;
                recordUsage(serviceName);

                if (immunitySystem.isCodeInfected(generatedCode)) {
                    log.error("-> [Orchestrator] AI generated toxic/broken code! Rejecting...");
                    aiProfiler.recordPerformance(taskCategory, finalProviderId, false, timeTaken);
                    
                    if (enhancedLearningService != null) {
                        Map<String, Object> requestMeta = new HashMap<>();
                        requestMeta.put("taskCategory", taskCategory);
                        requestMeta.put("errorSignature", errorSignature);
                        requestMeta.put("infected", true);
                        enhancedLearningService.learnFromAPIUsage("generateCode", finalProviderId, timeTaken, false, requestMeta).subscribe();
                    }
                    return tryNextProvider(chain, index + 1, taskCategory, errorSignature, prompt, userId);
                }

                return knowledgeBase.recordSuccessWithPermission(errorSignature, generatedCode, finalProviderId, timeTaken, 0.95)
                    .then(Mono.fromRunnable(() -> aiProfiler.recordPerformance(taskCategory, finalProviderId, true, timeTaken)))
                    .then(Mono.defer(() -> {
                        if (enhancedLearningService != null) {
                            Map<String, Object> requestMeta = new HashMap<>();
                            requestMeta.put("taskCategory", taskCategory);
                            requestMeta.put("errorSignature", errorSignature);
                            requestMeta.put("codeLength", generatedCode != null ? generatedCode.length() : 0);
                            enhancedLearningService.learnFromAPIUsage("generateCode", finalProviderId, timeTaken, true, requestMeta).subscribe();
                        }
                        return Mono.just(generatedCode);
                    }));
            })
            .onErrorResume(e -> {
                long timeTaken = System.currentTimeMillis() - startTime;
                log.error("Error from provider: {} on task: {}", finalProviderId, taskCategory, e);
                aiProfiler.recordPerformance(taskCategory, finalProviderId, false, timeTaken);
                
                if (enhancedLearningService != null) {
                    Map<String, Object> requestMeta = new HashMap<>();
                    requestMeta.put("taskCategory", taskCategory);
                    requestMeta.put("errorSignature", errorSignature);
                    requestMeta.put("errorMessage", e.getMessage());
                    enhancedLearningService.learnFromAPIUsage("generateCode", finalProviderId, timeTaken, false, requestMeta).subscribe();
                }
                return tryNextProvider(chain, index + 1, taskCategory, errorSignature, prompt, userId);
            });
    }

    private Mono<String> resolveApiKeyReactive(String userId, AIProviderType provider, com.supremeai.model.APIProvider dbProvider) {
        if (dbProvider != null) {
            return Mono.just(dbProvider.getApiKey());
        }
        if (userId == null || "system".equals(userId)) {
            return Mono.justOrEmpty(System.getenv(getEnvKeyForProvider(provider)));
        }
        return keyRotationService.selectBestKey(userId, getServiceNameForProvider(provider))
            .map(key -> keyRotationService.getDecryptedApiKey(key))
            .defaultIfEmpty(System.getenv(getEnvKeyForProvider(provider)));
    }

    private boolean isServiceQuotaAvailable(String serviceName) {
        if (quotaManager.getQuotaStatus(serviceName, "Requests") == null) return true;
        return quotaManager.getQuotaStatus(serviceName, "Requests").getRemainingQuota() > 0;
    }

    private void recordUsage(String serviceName) {
        quotaManager.recordUsage(serviceName, "Requests", 1);
    }

    private String getServiceNameForProvider(AIProviderType provider) {
        if (provider == null) return "Unknown";
        switch (provider) {
            case GROQ_LLAMA3: return "Groq";
            case GEMINI_PRO: return "Google";
            case ANTHROPIC_CLAUDE: return "Anthropic";
            case HUGGINGFACE_FREE: return "HuggingFace";
            case OPENAI: return "OpenAI";
            case DEEPSEEK: return "DeepSeek";
            case KIMI: return "Kimi";
            case MISTRAL: return "Mistral";
            case STEPFUN: return "StepFun";
            case OLLAMA: return "Ollama";
            case CLOUD_QWEN: return "GCP_Qwen";
            case CLOUD_LLAMA: return "GCP_Llama";
            case CLOUD_DEEPSEEK: return "HF_DeepSeek";
            case CLOUD_PHI: return "GCP_Phi";
            case CLOUD_NOMIC: return "GCP_Nomic";
            default: return "AI_Provider";
        }
    }

    private String getEnvKeyForProvider(AIProviderType provider) {
        if (provider == null) return "AI_API_KEY";
        switch (provider) {
            case GROQ_LLAMA3: return "GROQ_API_KEY";
            case GEMINI_PRO: return "GEMINI_API_KEY";
            case ANTHROPIC_CLAUDE: return "ANTHROPIC_API_KEY";
            case HUGGINGFACE_FREE: return "HUGGINGFACE_API_KEY";
            case OPENAI: return "OPENAI_API_KEY";
            case DEEPSEEK: return "DEEPSEEK_API_KEY";
            case KIMI: return "KIMI_API_KEY";
            case MISTRAL: return "MISTRAL_API_KEY";
            case STEPFUN: return "STEPFUN_API_KEY";
            case OLLAMA: return null;
            case CLOUD_QWEN:
            case CLOUD_LLAMA:
            case CLOUD_DEEPSEEK:
            case CLOUD_PHI:
            case CLOUD_NOMIC: return "SUPREME_CLOUD_API_KEY";
            default: return "AI_API_KEY";
        }
    }

    private String callAIProvider(AIProviderType provider, String apiKey, String prompt) throws Exception {
        String providerName = mapFallbackProviderToFactoryName(provider);
        com.supremeai.provider.AIProvider realProvider = providerFactory.getProvider(providerName, apiKey);
        // Note: Keeping .block() here since it's wrapped in Mono.fromCallable in tryNextProvider
        return realProvider.generate(prompt).block();
    }

    private String mapFallbackProviderToFactoryName(AIProviderType provider) {
        if (provider == null) return "unknown";
        switch (provider) {
            case GROQ_LLAMA3: return "groq";
            case GEMINI_PRO: return "gemini";
            case ANTHROPIC_CLAUDE: return "anthropic";
            case HUGGINGFACE_FREE: return "huggingface";
            case OPENAI: return "openai";
            case DEEPSEEK: return "deepseek";
            case KIMI: return "kimi";
            case MISTRAL: return "mistral";
            case STEPFUN: return "stepfun";
            case OLLAMA: return "ollama";
            case CLOUD_QWEN: return "gcp_qwen";
            case CLOUD_LLAMA: return "gcp_llama";
            case CLOUD_DEEPSEEK: return "hf_deepseek";
            case CLOUD_PHI: return "gcp_phi";
            case CLOUD_NOMIC: return "gcp_nomic";
            default: return provider.name().toLowerCase();
        }
    }

    public Map<String, Object> getProviderHealthStatus() {
        Map<String, Object> status = new java.util.HashMap<>();
        for (AIProviderType provider : allProviders) {
            CircuitBreaker cb = getOrCreateCircuitBreaker(provider.name().toLowerCase());
            Map<String, Object> providerStatus = new java.util.HashMap<>();
            if (cb != null) {
                providerStatus.put("state", cb.getState().name());
                providerStatus.put("failureRate", cb.getMetrics().getFailureRate());
                providerStatus.put("slowCallRate", cb.getMetrics().getSlowCallRate());
                providerStatus.put("numberOfSuccessfulCalls", cb.getMetrics().getNumberOfSuccessfulCalls());
                providerStatus.put("numberOfFailedCalls", cb.getMetrics().getNumberOfFailedCalls());
            } else {
                providerStatus.put("state", "UNKNOWN");
            }
            providerStatus.put("quotaAvailable", isServiceQuotaAvailable(getServiceNameForProvider(provider)));
            status.put(provider.name(), providerStatus);
        }
        return status;
    }
}
