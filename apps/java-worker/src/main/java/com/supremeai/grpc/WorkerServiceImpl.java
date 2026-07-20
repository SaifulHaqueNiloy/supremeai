package com.supremeai.grpc;

import com.supremeai.models.TaskEntity;
import com.supremeai.models.AuditEntity;
import com.supremeai.repositories.TaskRepository;
import com.supremeai.repositories.AuditRepository;
import com.supremeai.tasks.TaskProcessingService;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.Optional;

@GrpcService
public class WorkerServiceImpl extends WorkerServiceGrpc.WorkerServiceImplBase {

    private static final Logger logger = LoggerFactory.getLogger(WorkerServiceImpl.class);

    @Autowired
    private TaskRepository taskRepository;

    @Autowired
    private AuditRepository auditRepository;

    @Autowired
    private TaskProcessingService taskProcessingService;

    @Override
    public void submitTask(TaskRequest request, StreamObserver<TaskResponse> responseObserver) {
        logger.info("Received SubmitTask request of type: {}", request.getTaskType());

        TaskEntity task = new TaskEntity();
        task.setTaskType(request.getTaskType());
        task.setPayloadJson(request.getPayloadJson());
        task.setRequestedBy(request.getRequestedBy());
        task.setStatus("QUEUED");

        task = taskRepository.save(task);

        // বাংলা মন্তব্য: আগে এখানে শুধু একটা TODO কমেন্ট ছিল — টাস্ক QUEUED অবস্থায়
        // চিরকাল আটকে থাকত, কোনো error ছাড়াই। এখন সত্যিই async প্রসেসিং শুরু হয়;
        // gRPC caller-কে ব্লক না করেই (fire-and-forget, status getTaskStatus() দিয়ে
        // পরে চেক করা যাবে)।
        taskProcessingService.processAsync(task.getId());

        TaskResponse response = TaskResponse.newBuilder()
                .setTaskId(task.getId())
                .setStatus(task.getStatus())
                .setMessage("Task queued successfully")
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void getTaskStatus(TaskStatusRequest request, StreamObserver<TaskStatusResponse> responseObserver) {
        Optional<TaskEntity> taskOpt = taskRepository.findById(request.getTaskId());

        TaskStatusResponse.Builder responseBuilder = TaskStatusResponse.newBuilder()
                .setTaskId(request.getTaskId());

        if (taskOpt.isPresent()) {
            TaskEntity task = taskOpt.get();
            responseBuilder.setStatus(task.getStatus());
            if (task.getResultJson() != null) {
                responseBuilder.setResultJson(task.getResultJson());
            }
            if (task.getErrorMessage() != null) {
                responseBuilder.setErrorMessage(task.getErrorMessage());
            }
        } else {
            responseBuilder.setStatus("NOT_FOUND")
                           .setErrorMessage("Task ID not found in database");
        }

        responseObserver.onNext(responseBuilder.build());
        responseObserver.onCompleted();
    }

    @Override
    public void logAuditEvent(AuditLogRequest request, StreamObserver<AuditLogResponse> responseObserver) {
        logger.info("AUDIT LOG | Event: {} | User: {} | Resource: {}",
                request.getEventType(), request.getUserId(), request.getResource());

        // বাংলা মন্তব্য: অডিট লগ ডাটাবেসে supreme_audit_logs টেবিলে সংরক্ষণ করা হচ্ছে।
        try {
            AuditEntity audit = new AuditEntity();
            audit.setEventType(request.getEventType());
            audit.setUserId(request.getUserId());
            audit.setResource(request.getResource());
            auditRepository.save(audit);
        } catch (Exception e) {
            logger.error("Failed to persist audit log: {}", e.getMessage());
        }

        AuditLogResponse response = AuditLogResponse.newBuilder()
                .setSuccess(true)
                .setMessage("Audit log recorded")
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}
