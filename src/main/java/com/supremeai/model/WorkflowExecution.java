package com.supremeai.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class WorkflowExecution {
    private String executionId;
    private String workflowId;
    private String status; // RUNNING, COMPLETED, FAILED
    private int currentStepIndex;
    private Map<String, Object> stepResults;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private String errorMessage;

    public WorkflowExecution(String executionId, String workflowId, String status) {
        this.executionId = executionId;
        this.workflowId = workflowId;
        this.status = status;
        this.startedAt = LocalDateTime.now();
    }
}
