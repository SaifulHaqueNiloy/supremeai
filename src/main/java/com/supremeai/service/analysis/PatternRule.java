package com.supremeai.service.analysis;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.regex.Pattern;

/**
 * Represents a single pattern rule.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PatternRule {
    private String category;
    private Pattern pattern;
    private String message;
    private String suggestion;
}
