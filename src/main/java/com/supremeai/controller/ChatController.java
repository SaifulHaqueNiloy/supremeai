package com.supremeai.controller;

import com.supremeai.service.AutonomousQuestioningEngine;
import com.supremeai.service.MultiAIVotingService;
import com.supremeai.service.MultiAIConsensusService;
import com.supremeai.service.EnhancedLearningService;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.retry.Retry;
import io.github.resilience4j.retry.RetryRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;
import com.supremeai.dto.ChatRequest;
import com.supremeai.dto.FeedbackRequest;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private static final Logger logger = LoggerFactory.getLogger(ChatController.class);

    @Autowired(required = false)
    private MultiAIVotingService consensusService;

    @Autowired
    private AutonomousQuestioningEngine questioningEngine;

    @Autowired
    private MultiAIVotingService votingService;

    @Autowired(required = false)
    private EnhancedLearningService enhancedLearningService;

    @Autowired
    private com.supremeai.service.ChatIntelligenceService intelligenceService;

    private final CircuitBreaker aiCircuitBreaker;
    private final Retry aiRetry;

    public ChatController() {
        // Initialize circuit breaker and retry for AI operations
        this.aiCircuitBreaker = CircuitBreaker.ofDefaults("aiVotingService");
        this.aiRetry = Retry.ofDefaults("aiVotingService");
    }

    @PostMapping("/send")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN', 'AGENT_MANAGER', 'GUEST')")
    public Mono<ResponseEntity<Object>> sendMessage(@Valid @RequestBody ChatRequest request) {
        String message = request.getMessage();
        boolean skipValidation = request.isSkipValidation();

        if (message == null || message.trim().isEmpty()) {
            return Mono.just(ResponseEntity.badRequest().body(Map.of("error", "Message is required")));
        }

        logger.info("Received chat message: {}", message);

        // S3: Autonomous Questioning - Validate input clarity
        Mono<Object> validationMono = skipValidation ? Mono.empty() : 
            questioningEngine.validateAndQuestion(message, AutonomousQuestioningEngine.RequestType.GENERAL_AI)
                .flatMap(validation -> {
                    if (!validation.isComplete() && validation.hasQuestions()) {
                        Map<String, Object> response = new HashMap<>();
                        response.put("type", "CLARIFICATION_REQUIRED");
                        response.put("questions", validation.getClarifyingQuestions());
                        response.put("clarityScore", validation.getClarityScore());
                        response.put("message", "I need more information before I can give you a quality answer.");
                        return Mono.just(response);
                    }
                    return Mono.empty();
                });

        return validationMono
            .map(ResponseEntity::ok)
            .switchIfEmpty(
                // S4: 10-AI Voting System - Execute voting across models
                votingService.executeEnsembleVoting(message, null, 15000L)
                    .flatMap(votingResult -> {
                        String bestResponse = votingResult.getBestResponse();
                        Double confidence = votingResult.getAverageConfidence();

                        Map<String, Object> response = new HashMap<>();
                        response.put("message", bestResponse);
                        response.put("verdict", votingResult.getVerdict());
                        response.put("confidence", confidence);
                        response.put("modelsUsed", votingResult.getTotalModelsUsed());
                        response.put("processingTimeMs", votingResult.getProcessingTimeMs());
                        response.put("timestamp", java.time.Instant.now().toString());

                        // Intent classification (logic-only, so synchronous is okay but we wrap for safety)
                        var intent = intelligenceService.classifyIntent(message);
                        response.put("mode", intent.name().toLowerCase());
                        response.put("intent", intent.name());

                        // Chain side-effects (handleIntelligence and learning)
                        Mono<Void> sideEffects = intelligenceService.handleIntelligence(
                            request.getAgentId() != null ? request.getAgentId() : "default",
                            message,
                            intent,
                            "ADMIN",
                            confidence
                        );

                        if (enhancedLearningService != null) {
                            sideEffects = sideEffects.then(
                                enhancedLearningService.learnFromNLPInteraction(
                                    message,
                                    bestResponse,
                                    "voting_system",
                                    confidence != null ? confidence : 0.5,
                                    Map.of("modelsUsed", votingResult.getTotalModelsUsed())
                                ).then()
                            );
                        }

                        return sideEffects.thenReturn(ResponseEntity.ok((Object)response));
                    })
                    // Apply Circuit Breaker and Retry to the voting process
                    .transformDeferred(io.github.resilience4j.reactor.circuitbreaker.operator.CircuitBreakerOperator.of(aiCircuitBreaker))
                    .transformDeferred(io.github.resilience4j.reactor.retry.RetryOperator.of(aiRetry))
                    .onErrorResume(e -> {
                        logger.error("Failed to get response via voting system after retries", e);
                        
                        CircuitBreaker.State circuitState = aiCircuitBreaker.getState();
                        logger.warn("AI Circuit breaker state: {}", circuitState);

                        if (consensusService != null && circuitState != CircuitBreaker.State.OPEN) {
                            return consensusService.askConsensus(message,
                                java.util.Arrays.asList("groq", "deepseek", "claude", "openai", "ollama"), 10000L)
                                .map(res -> ResponseEntity.ok(Map.of(
                                    "message", res.getConsensusAnswer(),
                                    "confidence", res.getAverageConfidence(),
                                    "fallback", true,
                                    "circuitBreakerState", circuitState.name()
                                )));
                        }

                        return Mono.just(ResponseEntity.status(503).body(Map.of(
                            "error", "AI services temporarily unavailable",
                            "circuitBreakerState", circuitState.name(),
                            "retryAfter", 60
                        )));
                    })
            );
    }

    @GetMapping("/history")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN', 'GUEST')")
    public Mono<ResponseEntity<Object>> getHistory(
            @RequestParam(required = false) String agent,
            @RequestParam(defaultValue = "50") int limit) {
        return Mono.just(ResponseEntity.ok(Map.of(
            "messages", new ArrayList<>(),
            "count", 0,
            "agent", agent != null ? agent : "default"
        )));
    }

    @PostMapping("/feedback")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN', 'AGENT_MANAGER', 'GUEST')")
    public Mono<ResponseEntity<Object>> submitFeedback(@Valid @RequestBody FeedbackRequest request) {
        String messageId = request.getMessageId();
        boolean helpful = request.isHelpful();
        String userMessage = request.getUserMessage();
        String aiResponse = request.getAiResponse();

        logger.info("Received feedback for message: {}, helpful: {}", messageId, helpful);

        // Capture learning from feedback - this is valuable for NLP improvement
        if (enhancedLearningService != null && userMessage != null && aiResponse != null) {
            double qualityScore = helpful ? 1.0 : 0.3;
            enhancedLearningService.learnFromNLPInteraction(
                    userMessage,
                    aiResponse,
                    "feedback_system",
                    qualityScore,
                    Map.of("messageId", messageId, "helpful", helpful)
            ).subscribe(); // Fire and forget
        }

        return Mono.just(ResponseEntity.ok(Map.of("status", "received")));
    }

    /**
     * ডায়নামিকভাবে মোড সনাক্ত করার হেল্পার মেথড
     */
    private String detectMode(String message) {
        String lowerMsg = message.toLowerCase();
        if (lowerMsg.contains("architect") || lowerMsg.contains("design") || lowerMsg.contains("structure")) {
            return "architect";
        } else if (lowerMsg.contains("debug") || lowerMsg.contains("fix") || lowerMsg.contains("error") || lowerMsg.contains("issue")) {
            return "debug";
        } else if (lowerMsg.contains("review") || lowerMsg.contains("audit") || lowerMsg.contains("analyze")) {
            return "review";
        } else if (lowerMsg.contains("ask") || lowerMsg.contains("what") || lowerMsg.contains("how") || lowerMsg.contains("explain")) {
            return "ask";
        } else if (lowerMsg.contains("orchestrate") || lowerMsg.contains("manage") || lowerMsg.contains("coordinate")) {
            return "orchestrator";
        } else {
            return "code";
        }
    }

    @GetMapping("/health")
    public Mono<ResponseEntity<Object>> health() {
        return Mono.just(ResponseEntity.ok(Map.of(
            "status", "UP",
            "autonomous_questioning", "ACTIVE",
            "voting_system", "ACTIVE"
        )));
    }
}
