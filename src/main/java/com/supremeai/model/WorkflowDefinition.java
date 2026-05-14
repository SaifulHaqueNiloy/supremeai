package com.supremeai.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class WorkflowDefinition {
    private String id;
    private String name;
    private String description;
    private String trigger; // manual, scheduled, webhook
    private List<WorkflowStep> steps;
    private Map<String, Object> outputs;
}
