package com.supremeai.model.analysis;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.spring.data.firestore.Document;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.Map;

/**
 * Represents an analysis job entity for Firestore storage.
 */
@Document(collectionName = "analysis_jobs")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisJob {
    @DocumentId
    private String id;
    private String projectName;
    private String projectType;
    private String gitUrl;
    private String status; // PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    private Instant startTime;
    private Instant endTime;
    private Long durationMs;
    private String errorMessage;
    private int filesAnalyzed;
    private int totalFindings;
    private Map<String, Integer> findingsBySeverity;
    private boolean completed;
    private String initiatedBy;
}
