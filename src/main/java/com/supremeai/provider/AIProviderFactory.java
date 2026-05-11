package com.supremeai.provider;

import com.supremeai.service.AIProviderService;
import com.supremeai.service.ContextualAIRankingService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.context.annotation.Lazy;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Factory for creating AI provider instances
 * Supports AI models for voting system (S4)
 */
@Component
public class AIProviderFactory {

    private static final Logger logger = LoggerFactory.getLogger(AIProviderFactory.class);

    @Autowired
    private AIProviderService aiProviderService;

    @Autowired
    @Lazy
    private ContextualAIRankingService contextualRankingService;

    @Autowired(required = false)
    private OllamaProvider ollamaProvider;

    // Cache for provider health status
    private final Map<String, Boolean> providerHealthCache = new ConcurrentHashMap<>();

    public AIProvider getProvider(String name) {
        return getProvider(name, null);
    }

    public AIProvider getProvider(String name, String overrideApiKey) {
        String key = (overrideApiKey != null && !overrideApiKey.isEmpty()) 
                     ? overrideApiKey 
                     : aiProviderService.getActiveKey(name.toLowerCase());

        switch (name.toLowerCase()) {
            // Core AI Models for S4 Voting System
            case "gpt4":
            case "openai":
                return new OpenAIProvider(key);

            case "claude":
            case "anthropic":
                return new AnthropicProvider(key);

            case "gemini":
                return new GeminiProvider(key);

            case "groq":
                return new GroqProvider(key);

            case "deepseek":
                return new DeepSeekProvider(key);

            case "ollama":
                if (ollamaProvider == null) {
                    logger.error("Ollama provider bean not found. Add @Profile exclusion or enable in config.");
                    throw new IllegalStateException("Ollama provider not available. Check Spring configuration.");
                }
                return ollamaProvider;

            case "huggingface":
                return new HuggingFaceProvider(key);

            case "kimi":
                return new KimiProvider(key);

            case "mistral":
                return new MistralProvider(key);

            case "stepfun":
                return new StepFunProvider(key);

            case "codegeex4":
                return new CodeGeeX4Provider(key);

            case "gcp_qwen":
                return new SupremeCloudProvider(key, "gcp_qwen", "qwen2.5-coder:7b", "https://supreme-ai-qwen-coder-565236080752.us-central1.run.app");
            case "gcp_llama":
                return new SupremeCloudProvider(key, "gcp_llama", "llama3.1:8b", "https://supreme-ai-llama-3-1-565236080752.us-central1.run.app");
            case "gcp_phi":
                return new SupremeCloudProvider(key, "gcp_phi", "phi3", "https://supreme-ai-phi-3-565236080752.us-central1.run.app");
            case "gcp_nomic":
                return new SupremeCloudProvider(key, "gcp_nomic", "nomic-embed-text", "https://supreme-ai-nomic-embed-565236080752.us-central1.run.app");
            case "hf_deepseek":
                return new SupremeCloudProvider(key, "hf_deepseek", "deepseek-coder-v2", "https://supreme-ai-deepseek-pro-565236080752.us-central1.run.app");
            
            // HuggingFace Serverless Inference Endpoints (uses HF Inference API format)
            case "hf_mistral":
                return new SupremeCloudProvider(key, "hf_mistral", "mistralai/Mistral-7B-Instruct-v0.3", "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3");
            case "hf_llama":
                return new SupremeCloudProvider(key, "hf_llama", "meta-llama/Meta-Llama-3-8B-Instruct", "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct");
            case "hf_codellama":
                return new SupremeCloudProvider(key, "hf_codellama", "codellama/CodeLlama-7B-Instruct-hf", "https://api-inference.huggingface.co/models/codellama/CodeLlama-7B-Instruct-hf");
            case "hf_phi":
                return new SupremeCloudProvider(key, "hf_phi", "microsoft/Phi-3-mini-4k-instruct", "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct");
            
            // Render Free Tier Endpoints (configure URLs via environment)
            case "render_tinyllama":
                return new SupremeCloudProvider(key, "render_tinyllama", "tinyllama-1.1b", System.getenv().getOrDefault("RENDER_TINYLLAMA_URL", "https://tinyllama.onrender.com"));
            case "render_phi3":
                return new SupremeCloudProvider(key, "render_phi3", "phi-3-mini", System.getenv().getOrDefault("RENDER_PHI3_URL", "https://phi3.onrender.com"));
            case "render_phi2":
                return new SupremeCloudProvider(key, "render_phi2", "phi-2", System.getenv().getOrDefault("RENDER_PHI2_URL", "https://phi2.onrender.com"));
            case "render_qwen":
                return new SupremeCloudProvider(key, "render_qwen", "qwen-0.5b", System.getenv().getOrDefault("RENDER_QWEN_URL", "https://qwen.onrender.com"));

            // HuggingFace Specialized Models (Vision & Embedding)
            case "hf_phi_vision":
                return new SupremeCloudProvider(key, "hf_phi_vision", "microsoft/Phi-3-vision-128k-instruct", "https://api-inference.huggingface.co/models/microsoft/Phi-3-vision-128k-instruct");
            case "hf_paligemma":
                return new SupremeCloudProvider(key, "hf_paligemma", "google/paligemma-3b-mix-448", "https://api-inference.huggingface.co/models/google/paligemma-3b-mix-448");
            case "hf_e5_large":
                return new SupremeCloudProvider(key, "hf_e5_large", "intfloat/multilingual-e5-large", "https://api-inference.huggingface.co/models/intfloat/multilingual-e5-large");
            case "hf_bge":
                return new SupremeCloudProvider(key, "hf_bge", "BAAI/bge-large-en-v1.5", "https://api-inference.huggingface.co/models/BAAI/bge-large-en-v1.5");

            default:
                throw new IllegalArgumentException("Unknown AI provider: " + name + ". Supported: gpt4, claude, gemini, groq, deepseek, ollama, huggingface, kimi, mistral, stepfun, codegeex4, gcp_qwen, gcp_llama, gcp_phi, gcp_nomic, hf_deepseek, hf_mistral, hf_llama, hf_codellama, hf_phi, hf_phi_vision, hf_paligemma, hf_e5_large, hf_bge, render_tinyllama, render_phi3, render_phi2, render_qwen");
        }
    }

    /**
     * Get the best provider for a specific task type based on rankings and health
     * @param taskType Type of task (e.g., "code_generation", "code_analysis", "question_answering")
     * @return Best available AI provider for the task
     */
    public AIProvider getBestProviderForTask(String taskType) {
        logger.debug("Finding best provider for task: {}", taskType);

        // Try to get ranked providers for this task
        try {
            ContextualAIRankingService.TaskType rankingTaskType = ContextualAIRankingService.TaskType.QUESTION_ANSWERING;
            try {
                rankingTaskType = ContextualAIRankingService.TaskType.valueOf(taskType.toUpperCase());
            } catch (IllegalArgumentException ignored) {}

            List<ContextualAIRankingService.ProviderRanking> rankings = contextualRankingService.getRankingsForTask(rankingTaskType);

            if (rankings != null && !rankings.isEmpty()) {
                // Try providers in order of ranking
                for (ContextualAIRankingService.ProviderRanking ranking : rankings) {
                    try {
                        AIProvider provider = getProvider(ranking.provider);
                        if (isProviderHealthy(provider)) {
                            logger.info("Using ranked provider {} for task {}", ranking.provider, taskType);
                            return provider;
                        }
                    } catch (Exception e) {
                        logger.warn("Ranked provider {} unavailable: {}", ranking.provider, e.getMessage());
                    }
                }
            }
        } catch (Exception e) {
            logger.warn("Failed to get provider rankings for task {}: {}", taskType, e.getMessage());
        }

        // Fall back to default provider
        logger.info("No ranked providers available for task {}, using default", taskType);
        return getDefaultProvider();
    }

    /**
     * Get the default/healthiest available provider
     * @return A working AI provider
     */
    public AIProvider getDefaultProvider() {
        // Preferred providers in order (free tier first)
        String[] preferredProviders = {"gcp_qwen", "hf_deepseek", "hf_mistral", "hf_llama", "hf_codellama", "hf_phi", "hf_phi_vision", "hf_paligemma", "hf_e5_large", "gemini", "groq", "huggingface", "codegeex4", "stepfun", "deepseek", "gpt4", "claude", "mistral", "render_tinyllama", "render_phi3", "render_phi2", "render_qwen"};

        // Try preferred providers first
        for (String providerName : preferredProviders) {
            try {
                AIProvider provider = getProvider(providerName);
                if (isProviderHealthy(provider)) {
                    logger.info("Using {} as default provider", providerName);
                    return provider;
                }
            } catch (Exception e) {
                logger.warn("Preferred provider {} unavailable: {}", providerName, e.getMessage());
            }
        }

        // Try all supported providers
        for (String providerName : getSupportedProviders()) {
            try {
                AIProvider provider = getProvider(providerName);
                if (isProviderHealthy(provider)) {
                    logger.info("Using {} as fallback default provider", providerName);
                    return provider;
                }
            } catch (Exception e) {
                logger.debug("Provider {} unavailable: {}", providerName, e.getMessage());
            }
        }

        throw new RuntimeException("No working AI provider available");
    }

    /**
     * Check if a provider is healthy and responsive
     * @param provider The provider to check
     * @return true if the provider is healthy
     */
    private boolean isProviderHealthy(AIProvider provider) {
        String providerName = provider.getName();

        // Check cache first
        if (providerHealthCache.containsKey(providerName)) {
            return providerHealthCache.get(providerName);
        }

        // Perform health check
        try {
            String testResponse = provider.generate("test").block();
            boolean isHealthy = testResponse != null && !testResponse.isEmpty();
            providerHealthCache.put(providerName, isHealthy);
            return isHealthy;
        } catch (Exception e) {
            logger.debug("Health check failed for {}: {}", providerName, e.getMessage());
            providerHealthCache.put(providerName, false);
            return false;
        }
    }

    /**
     * Get list of all supported provider names
     */
    public String[] getSupportedProviders() {
        return new String[]{"gpt4", "claude", "gemini", "groq", "deepseek", "ollama", "huggingface", "kimi", "mistral", "stepfun", "codegeex4", "gcp_qwen", "gcp_llama", "gcp_phi", "gcp_nomic", "hf_deepseek", "hf_mistral", "hf_llama", "hf_codellama", "hf_phi", "hf_phi_vision", "hf_paligemma", "hf_e5_large", "hf_bge", "render_tinyllama", "render_phi3", "render_phi2", "render_qwen"};
    }

    /**
     * Get list of all supported provider names (alias for getSupportedProviders)
     */
    public String[] getAllProviderNames() {
        return getSupportedProviders();
    }

    /**
     * Get all available provider instances
     * @return List of all provider instances
     */
    public List<AIProvider> getAllProviders() {
        List<AIProvider> providers = new ArrayList<>();
        for (String providerName : getSupportedProviders()) {
            try {
                providers.add(getProvider(providerName));
            } catch (Exception e) {
                logger.debug("Could not create provider instance for {}: {}", providerName, e.getMessage());
            }
        }
        return providers;
    }

    /**
     * Get all available provider IDs
     * @return List of provider IDs
     */
    public List<String> getAvailableProviderIds() {
        return Arrays.asList(getSupportedProviders());
    }

    /**
     * Clear the provider health cache
     */
    public void clearHealthCache() {
        providerHealthCache.clear();
        logger.info("Provider health cache cleared");
    }

    private String resolveKey(String override, String fallback) {
        return (override != null && !override.isEmpty()) ? override : fallback;
    }
}
