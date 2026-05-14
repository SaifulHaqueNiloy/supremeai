package com.supremeai.model.analysis;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.spring.data.firestore.Document;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Document(collectionName = "dependency_graphs")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DependencyGraph {
    @DocumentId
    private String id;
    private String projectId;
    private String file;
    private List<String> imports;
    private List<String> importedBy;
    private String updatedAt;
}
