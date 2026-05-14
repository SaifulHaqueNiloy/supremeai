package com.supremeai.service.analysis;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CodeChunkData {
    private String id;
    private String file;
    private int startLine;
    private int endLine;
    private String content;
    private String hash;
    private String language;
}
