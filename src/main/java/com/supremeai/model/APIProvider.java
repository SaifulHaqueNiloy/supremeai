package com.supremeai.model;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.spring.data.firestore.Document;
import com.fasterxml.jackson.annotation.JsonFormat;
import java.time.LocalDateTime;
import java.util.Date;
import java.util.List;

@Document(collectionName = "api_providers")
public class APIProvider {
    @DocumentId
    private String id;
    private String name;
    private String type;
    private String status;
    private String baseUrl;
    private String apiKey;
    private Double usageLimit;
    private Double currentUsage;
    
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private Date lastCheck;

    private String creatorEmail;
    private String accountEmail;

    private java.util.List<String> models = new java.util.ArrayList<>();
    private java.util.List<String> capabilities = new java.util.ArrayList<>();
    private java.util.List<String> languages = new java.util.ArrayList<>();
    private Integer priority = 10;
    
    private boolean canCommunicate = true;
    private boolean canExecuteTasks = true;
    private boolean canParticipateInVoting = true;
    private String deploymentSource = "API"; // API, GCLOUD, LOCAL, OLLAMA
    private java.util.List<String> assignedRoles = new java.util.ArrayList<>();

    /**
     * Auto-discovered capability scores (0.0 - 1.0)
     * Populated by ProviderCapabilityAnalyzer on registration
     * Key: task type, Value: capability score
     */
    private java.util.Map<String, Double> capabilityScores = new java.util.HashMap<>();

    /** When capabilities were last benchmarked */
    private java.util.Date lastBenchmarkedAt;

    /** Number of times this provider has been benchmarked */
    private Integer benchmarkCount = 0;

    // Auto-validation tracking fields
    private Integer consecutiveErrorDays;
    private LocalDateTime lastValidated;
    private LocalDateTime lastErrorDate;
    private String deadReason;
    private LocalDateTime deadAt;

    public APIProvider() {}

    public APIProvider(String id, String name, String type, String status) {
        this.id = id;
        this.name = name;
        this.type = type;
        this.status = status;
        this.lastCheck = new Date();
    }

    // Getters and Setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getBaseUrl() { return baseUrl; }
    public void setBaseUrl(String baseUrl) { this.baseUrl = baseUrl; }
    public String getApiKey() { return apiKey; }
    public void setApiKey(String apiKey) { this.apiKey = apiKey; }
    public Double getUsageLimit() { return usageLimit; }
    public void setUsageLimit(Double usageLimit) { this.usageLimit = usageLimit; }
    public Double getCurrentUsage() { return currentUsage; }
    public void setCurrentUsage(Double currentUsage) { this.currentUsage = currentUsage; }
    public Date getLastCheck() { return lastCheck; }
    public void setLastCheck(Date lastCheck) { this.lastCheck = lastCheck; }

    public java.util.List<String> getModels() { return models; }
    public void setModels(java.util.List<String> models) { this.models = models; }

    public java.util.List<String> getCapabilities() { return capabilities; }
    public void setCapabilities(java.util.List<String> capabilities) { this.capabilities = capabilities; }

    public java.util.List<String> getLanguages() { return languages; }
    public void setLanguages(java.util.List<String> languages) { this.languages = languages; }

    public Integer getPriority() { return priority; }
    public void setPriority(Integer priority) { this.priority = priority; }

    public String getCreatorEmail() { return creatorEmail; }
    public void setCreatorEmail(String creatorEmail) { this.creatorEmail = creatorEmail; }

    public String getAccountEmail() { return accountEmail; }
    public void setAccountEmail(String accountEmail) { this.accountEmail = accountEmail; }

    public boolean isCanCommunicate() { return canCommunicate; }
    public void setCanCommunicate(boolean canCommunicate) { this.canCommunicate = canCommunicate; }

    public boolean isCanExecuteTasks() { return canExecuteTasks; }
    public void setCanExecuteTasks(boolean canExecuteTasks) { this.canExecuteTasks = canExecuteTasks; }

    public boolean isCanParticipateInVoting() { return canParticipateInVoting; }
    public void setCanParticipateInVoting(boolean canParticipateInVoting) { this.canParticipateInVoting = canParticipateInVoting; }

    public String getDeploymentSource() { return deploymentSource; }
    public void setDeploymentSource(String deploymentSource) { this.deploymentSource = deploymentSource; }

    public Integer getConsecutiveErrorDays() { return consecutiveErrorDays; }
    public void setConsecutiveErrorDays(Integer consecutiveErrorDays) { this.consecutiveErrorDays = consecutiveErrorDays; }

    public LocalDateTime getLastValidated() { return lastValidated; }
    public void setLastValidated(LocalDateTime lastValidated) { this.lastValidated = lastValidated; }

    public LocalDateTime getLastErrorDate() { return lastErrorDate; }
    public void setLastErrorDate(LocalDateTime lastErrorDate) { this.lastErrorDate = lastErrorDate; }

    public String getDeadReason() { return deadReason; }
    public void setDeadReason(String deadReason) { this.deadReason = deadReason; }

    public java.util.List<String> getAssignedRoles() { return assignedRoles; }
    public void setAssignedRoles(java.util.List<String> assignedRoles) { this.assignedRoles = assignedRoles; }

    public LocalDateTime getDeadAt() { return deadAt; }
    public void setDeadAt(LocalDateTime deadAt) { this.deadAt = deadAt; }

    public java.util.Map<String, Double> getCapabilityScores() { return capabilityScores; }
    public void setCapabilityScores(java.util.Map<String, Double> capabilityScores) { this.capabilityScores = capabilityScores; }

    public java.util.Date getLastBenchmarkedAt() { return lastBenchmarkedAt; }
    public void setLastBenchmarkedAt(java.util.Date lastBenchmarkedAt) { this.lastBenchmarkedAt = lastBenchmarkedAt; }

    public Integer getBenchmarkCount() { return benchmarkCount; }
    public void setBenchmarkCount(Integer benchmarkCount) { this.benchmarkCount = benchmarkCount; }
}
