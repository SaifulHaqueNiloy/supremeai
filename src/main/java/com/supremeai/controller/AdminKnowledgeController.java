package com.supremeai.controller;

import com.supremeai.model.KnowledgeDomain;
import com.supremeai.model.KnowledgeRecommendation;
import com.supremeai.repository.KnowledgeDomainRepository;
import com.supremeai.repository.KnowledgeRecommendationRepository;
import com.supremeai.service.KnowledgeService;
import com.supremeai.response.ApiResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/admin/knowledge")
@PreAuthorize("hasRole('ADMIN')")
public class AdminKnowledgeController extends BaseAdminController<Object, String> {

    private final KnowledgeDomainRepository domainRepository;
    private final KnowledgeRecommendationRepository recommendationRepository;
    private final KnowledgeService knowledgeService;

    @Autowired
    public AdminKnowledgeController(KnowledgeDomainRepository domainRepository, 
                                    KnowledgeRecommendationRepository recommendationRepository,
                                    KnowledgeService knowledgeService) {
        this.domainRepository = domainRepository;
        this.recommendationRepository = recommendationRepository;
        this.knowledgeService = knowledgeService;
    }

    @GetMapping("/snapshot")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> getKnowledgeSnapshot() {
        return knowledgeService.getKnowledgeSnapshot()
                .map(data -> ResponseEntity.ok(ApiResponse.ok(data)));
    }

    @GetMapping("/domains")
    public Mono<ResponseEntity<ApiResponse<List<Map<String, Object>>>>> getDomains() {
        return domainRepository.findAll()
                .collectList()
                .map(list -> {
                    List<Map<String, Object>> uiDomains = list.stream().map(d -> Map.<String, Object>of(
                            "id", d.getId(),
                            "name", d.getName(),
                            "status", d.getStatus().name(),
                            "keywords", d.getKeywords(),
                            "knowledgeCount", d.getNodesDiscovered() != null ? d.getNodesDiscovered() : 0
                    )).collect(Collectors.toList());
                    
                    return ResponseEntity.ok(ApiResponse.ok(uiDomains));
                });
    }

    @PostMapping("/domains")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> createDomain(@RequestBody Map<String, Object> body) {
        String name = (String) body.get("name");
        List<String> keywords = (List<String>) body.get("keywords");
        
        if (name == null || name.isEmpty()) {
            return Mono.just(ResponseEntity.badRequest().body(ApiResponse.error("Name is required")));
        }

        KnowledgeDomain domain = new KnowledgeDomain(name, keywords != null ? keywords : List.of());
        return domainRepository.save(domain)
                .map(saved -> {
                    Map<String, Object> responseData = Map.of("domain", saved);
                    return ResponseEntity.ok(ApiResponse.ok(responseData));
                })
                .onErrorResume(e -> handleError("Failed to create domain", e));
    }

    @GetMapping("/recommendations")
    public Mono<ResponseEntity<ApiResponse<List<Map<String, Object>>>>> getRecommendations() {
        return recommendationRepository.findAll()
                .collectList()
                .map(list -> {
                    List<Map<String, Object>> uiRecs = list.stream().map(r -> Map.<String, Object>of(
                            "id", r.getId(),
                            "title", r.getTopic(),
                            "description", r.getReasoning(),
                            "confidence", r.getConfidence(),
                            "suggestedKeywords", r.getKeywords(),
                            "createdAt", r.getCreatedAt().toString()
                    )).collect(Collectors.toList());
                    
                    return ResponseEntity.ok(ApiResponse.ok(uiRecs));
                });
    }

    @PostMapping("/recommendations/{id}/approve")
    public Mono<ResponseEntity<ApiResponse<String>>> approveRecommendation(@PathVariable String id) {
        return recommendationRepository.findById(id)
                .flatMap(rec -> {
                    rec.setStatus(KnowledgeRecommendation.Status.APPROVED);
                    rec.setProcessedAt(LocalDateTime.now());
                    
                    // Logic to actually create a domain or trigger learning could go here
                    KnowledgeDomain newDomain = new KnowledgeDomain(rec.getTopic(), rec.getKeywords());
                    
                    return recommendationRepository.save(rec)
                            .then(domainRepository.save(newDomain))
                            .then(Mono.just(ResponseEntity.ok(ApiResponse.ok("Recommendation approved and domain created"))));
                })
                .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    @PostMapping("/recommendations/{id}/decline")
    public Mono<ResponseEntity<ApiResponse<String>>> declineRecommendation(@PathVariable String id) {
        return recommendationRepository.findById(id)
                .flatMap(rec -> {
                    rec.setStatus(KnowledgeRecommendation.Status.DECLINED);
                    rec.setProcessedAt(LocalDateTime.now());
                    return recommendationRepository.save(rec)
                            .then(Mono.just(ResponseEntity.ok(ApiResponse.ok("Recommendation declined"))));
                })
                .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    @PostMapping("/domains/{domainId}/start")
    public Mono<ResponseEntity<ApiResponse<KnowledgeDomain>>> startLearning(@PathVariable String domainId) {
        return knowledgeService.startLearning(domainId)
                .map(data -> ResponseEntity.ok(ApiResponse.ok(data)));
    }

    @PostMapping("/domains/{domainId}/process")
    public Mono<ResponseEntity<ApiResponse<Map<String, Object>>>> processLearning(@PathVariable String domainId) {
        return knowledgeService.processLearningJob(domainId)
                .map(data -> ResponseEntity.ok(ApiResponse.ok(data)));
    }

    @PostMapping("/recommendations/generate")
    public Mono<ResponseEntity<ApiResponse<List<KnowledgeRecommendation>>>> generateRecommendations() {
        return knowledgeService.generateRecommendations()
                .map(data -> ResponseEntity.ok(ApiResponse.ok(data)));
    }
}

