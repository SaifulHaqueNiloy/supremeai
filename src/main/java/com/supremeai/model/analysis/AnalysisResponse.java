package com.supremeai.model.analysis;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * Response DTO for analysis results.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResponse {
    private String jobId;
    private String status;
    private Long durationMs;
    private String project;
    private int filesAnalyzed;
    private int totalFiles;
    private int totalFindings;
    private Map<String, Integer> summary;
    private List<AnalysisFinding> findings;
    private List<AnalysisFix> fixes;
    private boolean completed;
    private String errorMessage;
    private boolean ragUsed;
    private boolean incrementalUsed;
    private int changedFiles;
    private int cachedFindings;
}
