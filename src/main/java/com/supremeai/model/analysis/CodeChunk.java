package com.supremeai.model.analysis;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.spring.data.firestore.Document;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Document(collectionName = "code_embeddings")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CodeChunk {
    @DocumentId
    private String id;
    private String projectId;
    private String file;
    private int startLine;
    private int endLine;
    private String content;
    private String hash;
    private String language;
    private List<Double> embedding;
    private String createdAt;
}
