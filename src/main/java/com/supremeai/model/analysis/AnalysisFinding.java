package com.supremeai.model.analysis;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.spring.data.firestore.Document;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Represents a single security/quality finding.
 */
@Document(collectionName = "analysis_findings")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisFinding {
    @DocumentId
    private String id;
    private String jobId;
    private String severity; // CRITICAL, HIGH, MEDIUM, LOW, INFO
    private String category; // SECRETS, SQL_INJECTION, XSS, PATH_TRAVERSAL, etc.
    private String file;
    private int line;
    private String message;
    private String suggestion;
    private String pattern;
    private String codeSnippet;
}
