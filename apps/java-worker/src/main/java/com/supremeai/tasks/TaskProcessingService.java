package com.supremeai.tasks;

import com.supremeai.models.TaskEntity;
import com.supremeai.repositories.TaskRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * বাংলা মন্তব্য: submitTask() এ সেভ হওয়া QUEUED টাস্ককে আসলে প্রসেস করার
 * দায়িত্ব এই সার্ভিসের। আগে এখানে শুধু একটা TODO কমেন্ট ছিল — টাস্ক DB-তে
 * QUEUED অবস্থায় চিরকাল আটকে থাকত, gRPC কল সফল রেসপন্স দিলেও বাস্তবে কিছুই
 * হতো না।
 *
 * এখন: রেজিস্টার্ড TaskHandler bean-গুলোর মধ্যে থেকে task_type ম্যাচ করা
 * handler-কে asynchronously কল করা হয়। কোনো handler রেজিস্টার্ড না থাকলে —
 * silently QUEUED রাখার বদলে honestly FAILED মার্ক করে স্পষ্ট error message
 * সেভ করা হয়, যাতে caller getTaskStatus() দিয়ে আসল অবস্থা জানতে পারে।
 */
@Service
public class TaskProcessingService {

    private static final Logger logger = LoggerFactory.getLogger(TaskProcessingService.class);

    @Autowired
    private TaskRepository taskRepository;

    private final Map<String, TaskHandler> handlersByType;

    @Autowired
    public TaskProcessingService(List<TaskHandler> handlers) {
        this.handlersByType = handlers.stream()
                .collect(Collectors.toMap(TaskHandler::getTaskType, h -> h, (a, b) -> a));
        if (handlersByType.isEmpty()) {
            logger.warn("No TaskHandler beans registered — all submitted tasks will fail with NO_HANDLER_REGISTERED until handlers are added.");
        }
    }

    @Async("taskExecutor")
    public void processAsync(String taskId) {
        Optional<TaskEntity> taskOpt = taskRepository.findById(taskId);
        if (taskOpt.isEmpty()) {
            logger.error("processAsync: task {} not found in DB, cannot process.", taskId);
            return;
        }

        TaskEntity task = taskOpt.get();
        TaskHandler handler = handlersByType.get(task.getTaskType());

        if (handler == null) {
            task.setStatus("FAILED");
            task.setErrorMessage("NO_HANDLER_REGISTERED for task_type='" + task.getTaskType() + "'");
            taskRepository.save(task);
            logger.error("Task {} failed: no TaskHandler registered for type '{}'.", taskId, task.getTaskType());
            return;
        }

        task.setStatus("PROCESSING");
        taskRepository.save(task);

        try {
            String resultJson = handler.handle(task);
            task.setStatus("COMPLETED");
            task.setResultJson(resultJson);
        } catch (Exception e) {
            logger.error("Task {} ({}) failed during handler execution.", taskId, task.getTaskType(), e);
            task.setStatus("FAILED");
            task.setErrorMessage(e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName());
        }

        taskRepository.save(task);
    }
}
