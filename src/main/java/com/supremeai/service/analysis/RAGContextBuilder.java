package com.supremeai.service.analysis;

import com.supremeai.model.analysis.CodeChunk;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
@Slf4j
public class RAGContextBuilder {

    private static final int DEFAULT_TOP_K = 10;
    private static final int MAX_TOKENS_PER_AGENT = 8000;
    private static final int CONTEXT_LINES = 5;
    private static final double AVG_TOKENS_PER_LINE = 4.0;

    private final VectorSearchService vectorSearchService;

    public RAGContextBuilder(VectorSearchService vectorSearchService) {
        this.vectorSearchService = vectorSearchService;
    }

    public RAGContext buildContext(String projectId, String agentQuery, List<String> allFiles) {
        return buildContext(projectId, agentQuery, allFiles, DEFAULT_TOP_K, MAX_TOKENS_PER_AGENT);
    }

     public RAGContext buildContext(String projectId, String agentQuery, List<String> allFiles, int topK, int maxTokens) {
         List<CodeChunk> relevantChunks = vectorSearchService.searchSimilarChunks(projectId, agentQuery, topK);

         if (relevantChunks.isEmpty()) {
             log.debug("No relevant chunks found for query, falling back to file scan");
             return new RAGContext(
                 agentQuery,
                 List.of(),
                 List.of(),
                 0,
                 0,
                 allFiles.size()
             );
         }

         List<ContextChunk> contextChunks = new ArrayList<>();
         int totalTokens = 0;

         for (CodeChunk chunk : relevantChunks) {
             int estimatedTokens = (int) (chunk.getContent().split("\n").length * AVG_TOKENS_PER_LINE);

             if (totalTokens + estimatedTokens > maxTokens) {
                 break;
             }

             contextChunks.add(new ContextChunk(
                 chunk.getFile(),
                 chunk.getStartLine(),
                 chunk.getEndLine(),
                 chunk.getContent(),
                 1.0
             ));

             totalTokens += estimatedTokens;
         }

         List<String> contextFiles = contextChunks.stream()
             .map(ContextChunk::getFile)
             .distinct()
             .collect(Collectors.toList());

         return new RAGContext(
             agentQuery,
             contextChunks,
             contextFiles,
             totalTokens,
             contextFiles.size(),
             allFiles.size()
         );
     }

     public RAGContext buildContextForFile(String projectId, String filePath, int maxTokens) {
         List<CodeChunk> chunks = vectorSearchService.searchSimilarChunks(projectId, filePath, DEFAULT_TOP_K);

         List<ContextChunk> contextChunks = chunks.stream()
             .filter(c -> c.getFile().equals(filePath))
             .map(c -> new ContextChunk(
                 c.getFile(),
                 c.getStartLine(),
                 c.getEndLine(),
                 c.getContent(),
                 1.0
             ))
             .collect(Collectors.toList());

         int totalTokens = (int) (contextChunks.stream()
             .mapToInt(c -> c.getContent().split("\n").length)
             .sum() * AVG_TOKENS_PER_LINE);

         return new RAGContext(
             "analyze:" + filePath,
             contextChunks,
             List.of(filePath),
             totalTokens,
             1,
             1
         );
     }

     @Data
     @NoArgsConstructor
     @AllArgsConstructor
     public static class RAGContext {
         private String agentQuery;
         private List<ContextChunk> relevantChunks;
         private List<String> contextFiles;
         private int totalTokens;
         private int filesScanned;
         private int totalFiles;
     }

     @Data
     @NoArgsConstructor
     @AllArgsConstructor
     public static class ContextChunk {
         private String file;
         private int startLine;
         private int endLine;
         private String content;
         private double relevanceScore;
     }
}
