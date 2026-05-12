package com.supremeai.model;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.firestore.annotation.ServerTimestamp;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * Reverse engineering job stored in Firestore.
 * Collection: "reverse_engineering_jobs"
 */
public class ReverseEngineeringJob {

    @DocumentId
    private String jobId;

    private String userId;

    private String websiteUrl;

    private String status; // PENDING, PROCESSING, COMPLETED, FAILED

    private String errorMessage;

    private Map<String, Object> discoveredApis; // endpoints, methods, params

    private Map<String, Object> scrapedData; // raw scraping results

    private String generatedAppId; // linked generated app

    @ServerTimestamp
    private LocalDateTime createdAt;

    @ServerTimestamp
    private LocalDateTime updatedAt;

    public ReverseEngineeringJob() {}

    public ReverseEngineeringJob(String jobId, String userId, String websiteUrl) {
        this.jobId = jobId;
        this.userId = userId;
        this.websiteUrl = websiteUrl;
        this.status = "PENDING";
        this.createdAt = LocalDateTime.now();
    }

    public String getJobId() { return jobId; }
    public void setJobId(String jobId) { this.jobId = jobId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public String getWebsiteUrl() { return websiteUrl; }
    public void setWebsiteUrl(String websiteUrl) { this.websiteUrl = websiteUrl; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }

    public Map<String, Object> getDiscoveredApis() { return discoveredApis; }
    public void setDiscoveredApis(Map<String, Object> discoveredApis) { this.discoveredApis = discoveredApis; }

    public Map<String, Object> getScrapedData() { return scrapedData; }
    public void setScrapedData(Map<String, Object> scrapedData) { this.scrapedData = scrapedData; }

    public String getGeneratedAppId() { return generatedAppId; }
    public void setGeneratedAppId(String generatedAppId) { this.generatedAppId = generatedAppId; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
