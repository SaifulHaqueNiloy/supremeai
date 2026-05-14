package com.supremeai.repository;

import com.supremeai.model.TaskProviderAssignment;
import com.google.cloud.spring.data.firestore.FirestoreReactiveRepository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * Repository for task-to-provider assignments.
 * Supports dynamic 0 to ∞ provider mappings per task.
 */
public interface TaskProviderAssignmentRepository
        extends FirestoreReactiveRepository<TaskProviderAssignment> {

    Flux<TaskProviderAssignment> findByTaskTypeAndIsActiveTrue(String taskType);

    Flux<TaskProviderAssignment> findAllByIsActiveTrue();

    Mono<TaskProviderAssignment> findByTaskType(String taskType);

    Mono<Long> countByIsActiveTrue();
}