package com.supremeai.service.analysis;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FixPromptTemplate {
    private String templateName;
    private String template;
    private String outputFormat;

    public String render(FixContext context) {
        return template
            .replace("{filePath}", context.getFilePath())
            .replace("{lineNumber}", String.valueOf(context.getLineNumber()))
            .replace("{findingMessage}", context.getFindingMessage())
            .replace("{suggestion}", context.getSuggestion())
            .replace("{codeSnippet}", context.getCodeSnippet())
            .replace("{severity}", context.getSeverity())
            .replace("{category}", context.getCategory())
            .replace("{language}", context.getLanguage());
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class FixContext {
        private String filePath;
        private int lineNumber;
        private String findingMessage;
        private String suggestion;
        private String codeSnippet;
        private String severity;
        private String category;
        private String language;
    }
}
