package com.supremeai.model;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.firestore.annotation.ServerTimestamp;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * Daily health report for all stored API keys.
 * Helps administrators identify dead/expired keys.
 */
public class APIHealthReport {

    @DocumentId
    private String id;

    private int totalKeysTested;
    private int activeKeys;
    private int deadKeys;
    private int rotationDueKeys;
    
    private List<Map<String, Object>> deadKeyDetails; // [{id, label, provider, error}]

    @ServerTimestamp
    private LocalDateTime createdAt;

    public APIHealthReport() {}

    public APIHealthReport(String id, int total, int active, int dead, int rotationDue) {
        this.id = id;
        this.totalKeysTested = total;
        this.activeKeys = active;
        this.deadKeys = dead;
        this.rotationDueKeys = rotationDue;
        this.createdAt = LocalDateTime.now();
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public int getTotalKeysTested() { return totalKeysTested; }
    public void setTotalKeysTested(int totalKeysTested) { this.totalKeysTested = totalKeysTested; }

    public int getActiveKeys() { return activeKeys; }
    public void setActiveKeys(int activeKeys) { this.activeKeys = activeKeys; }

    public int getDeadKeys() { return deadKeys; }
    public void setDeadKeys(int deadKeys) { this.deadKeys = deadKeys; }

    public int getRotationDueKeys() { return rotationDueKeys; }
    public void setRotationDueKeys(int rotationDueKeys) { this.rotationDueKeys = rotationDueKeys; }

    public List<Map<String, Object>> getDeadKeyDetails() { return deadKeyDetails; }
    public void setDeadKeyDetails(List<Map<String, Object>> deadKeyDetails) { this.deadKeyDetails = deadKeyDetails; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
