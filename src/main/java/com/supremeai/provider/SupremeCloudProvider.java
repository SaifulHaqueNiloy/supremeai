package com.supremeai.provider;

import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.core.type.TypeReference;

/**
 * Generic SupremeCloudProvider for all GCP Cloud Run, HF Inference Endpoints, and Render deployments.
 * Supports both OpenAI-compatible and HF Inference API formats.
 */
public class SupremeCloudProvider extends AbstractHttpProvider {

    private final String providerName;
    private final boolean isHfInference;

    public SupremeCloudProvider(String apiKey, String providerName, String defaultModel, String baseUrl) {
        super(apiKey, baseUrl, defaultModel);
        this.providerName = providerName;
        this.isHfInference = providerName.startsWith("hf_") && baseUrl.contains("api-inference.huggingface.co");
    }

    @Override
    public String getName() {
        return providerName;
    }

    @Override
    protected String getRequestUrl() {
        if (isHfInference) {
            return baseUrl; // HF inference uses URL directly
        }
        return baseUrl.endsWith("/") ? baseUrl + "api/generate" : baseUrl + "/api/generate";
    }

    @Override
    public Map<String, Object> getCapabilities() {
        return Map.of(
            "name", providerName,
            "model", getModel(),
            "type", isHfInference ? "huggingface-inference" : "cloud-native"
        );
    }

    @Override
    protected Map<String, Object> createRequestBody(String prompt) {
        if (isHfInference) {
            return Map.of(
                "inputs", prompt,
                "parameters", Map.of(
                    "max_new_tokens", 512,
                    "temperature", 0.7,
                    "return_full_text", false
                )
            );
        }
        return Map.of(
            "model", getModel(),
            "messages", List.of(Map.of("role", "user", "content", prompt)),
            "max_tokens", 1024,
            "temperature", 0.7
        );
    }

    @Override
    @SuppressWarnings("unchecked")
    protected String extractResponse(String responseBody) throws Exception {
        if (responseBody == null || responseBody.isBlank()) {
            return "No response from " + providerName;
        }
        
        if (isHfInference) {
            Map<String, Object> response = objectMapper.readValue(responseBody, new TypeReference<Map<String, Object>>() {});
            if (response.containsKey("generated_text")) {
                return (String) response.get("generated_text");
            }
            if (response.containsKey("error")) {
                return "HF Error: " + response.get("error");
            }
            return "Empty HF response";
        }
        
        Map<String, Object> response = objectMapper.readValue(responseBody, new TypeReference<Map<String, Object>>() {});
        List<Map<String, Object>> choices = (List<Map<String, Object>>) response.get("choices");
        if (choices != null && !choices.isEmpty()) {
            Map<String, Object> first = choices.get(0);
            Map<String, Object> message = (Map<String, Object>) first.get("message");
            if (message != null && message.get("content") != null) {
                return (String) message.get("content");
            }
        }
        return "Empty response from " + providerName;
    }

    @Override
    protected void addAuthHeaders(okhttp3.Request.Builder builder) {
        if (apiKey != null && !apiKey.isBlank()) {
            builder.addHeader("Authorization", "Bearer " + apiKey);
        }
    }
}