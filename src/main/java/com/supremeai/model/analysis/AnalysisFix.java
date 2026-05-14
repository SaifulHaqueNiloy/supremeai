package com.supremeai.model.analysis;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.spring.data.firestore.Document;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Document(collectionName = "analysis_fixes")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisFix {
    @DocumentId
    private String id;
    private String jobId;
    private String findingId;
    private String file;
    private int line;
    private String originalCode;
    private String fixedCode;
    private String explanation;
    private double confidence;
    private boolean applied;
    private String createdAt;
}
