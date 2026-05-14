package com.supremeai.model.analysis;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.spring.data.firestore.Document;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Document(collectionName = "analysis_baselines")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisBaseline {
    @DocumentId
    private String id;
    private String projectId;
    private String commitHash;
    private String findingsHash;
    private List<AnalysisFinding> findings;
    private String createdAt;
}
