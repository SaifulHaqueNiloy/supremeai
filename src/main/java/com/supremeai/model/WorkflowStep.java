package com.supremeai.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class WorkflowStep {
    private String id;
    private String agent; // ReverseEngineeringAgent, CodeGenerationAgent, etc.
    private Map<String, Object> input;
    private String output; // Key to store result for next steps
}
