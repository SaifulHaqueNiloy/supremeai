package com.supremeai.model.analysis;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.multipart.MultipartFile;

import java.time.Instant;
import java.util.Map;

/**
 * Represents an analysis job request.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisRequest {
    private String projectType;
    private String gitUrl;
    private String branch;
    private MultipartFile zipFile;
    private boolean includeDependencies;
    private Map<String, Boolean> agents;
    private Integer maxFiles;
    private Long maxSizeBytes;
    private boolean ragEnabled;
    private boolean incrementalEnabled;
    private boolean fixesEnabled;
    private String baselineCommit;
    private String projectId;
}
