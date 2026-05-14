package com.supremeai.service.analysis;

import com.supremeai.model.analysis.AnalysisBaseline;
import com.supremeai.model.analysis.AnalysisFinding;
import com.supremeai.repository.analysis.AnalysisBaselineRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.io.File;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

@Service
@Slf4j
public class IncrementalAnalysisService {

    private final GitDiffService gitDiffService;
    private final DependencyGraphService dependencyGraphService;
    private final AnalysisBaselineRepository baselineRepository;

    @Autowired
    public IncrementalAnalysisService(
            GitDiffService gitDiffService,
            DependencyGraphService dependencyGraphService,
            AnalysisBaselineRepository baselineRepository) {
        this.gitDiffService = gitDiffService;
        this.dependencyGraphService = dependencyGraphService;
        this.baselineRepository = baselineRepository;
    }

    public IncrementalAnalysisPlan createPlan(String projectId, String repoPath) throws Exception {
        String currentCommit = gitDiffService.getCurrentCommitHash(repoPath);

        AnalysisBaseline baseline = null;
        try {
            baseline = baselineRepository.findByProjectId(projectId)
                .sort((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                .blockFirst();
        } catch (Exception e) {
            log.debug("No baseline found for project {}", projectId);
        }

        if (baseline == null || baseline.getCommitHash() == null) {
            log.info("No baseline found for project {}. Full analysis required.", projectId);
            return IncrementalAnalysisPlan.builder()
                .projectId(projectId)
                .currentCommit(currentCommit)
                .baselineCommit(null)
                .fullAnalysis(true)
                .changedFiles(List.of())
                .impactedFiles(List.of())
                .cachedFindings(List.of())
                .build();
        }

        String baselineCommit = baseline.getCommitHash();
        if (baselineCommit.equals(currentCommit)) {
            log.info("Commit unchanged ({}). Returning cached results.", currentCommit);
            List<AnalysisFinding> cachedFindings = baseline.getFindings() != null ? baseline.getFindings() : List.of();
            return IncrementalAnalysisPlan.builder()
                .projectId(projectId)
                .currentCommit(currentCommit)
                .baselineCommit(baselineCommit)
                .fullAnalysis(false)
                .changedFiles(List.of())
                .impactedFiles(List.of())
                .cachedFindings(cachedFindings)
                .build();
        }

        List<String> changedFiles = gitDiffService.getChangedFiles(repoPath, baselineCommit, currentCommit);
        List<String> impactedFiles = dependencyGraphService.findImpactedFiles(projectId, changedFiles);
        Set<String> filesToAnalyze = new LinkedHashSet<>(impactedFiles);

        List<AnalysisFinding> cachedFindings = new ArrayList<>();
        if (baseline.getFindings() != null) {
            Set<String> changedAndImpacted = new HashSet<>(impactedFiles);
            for (AnalysisFinding finding : baseline.getFindings()) {
                if (finding.getFile() != null && !changedAndImpacted.contains(finding.getFile())) {
                    cachedFindings.add(finding);
                }
            }
        }

        log.info("Incremental analysis plan: {} changed, {} impacted, {} cached findings",
                changedFiles.size(), impactedFiles.size(), cachedFindings.size());

        return IncrementalAnalysisPlan.builder()
            .projectId(projectId)
            .currentCommit(currentCommit)
            .baselineCommit(baselineCommit)
            .fullAnalysis(false)
            .changedFiles(changedFiles)
            .impactedFiles(new ArrayList<>(filesToAnalyze))
            .cachedFindings(cachedFindings)
            .build();
    }

    public List<File> filterFilesToAnalyze(List<File> allFiles, IncrementalAnalysisPlan plan) {
        if (plan.isFullAnalysis()) {
            return allFiles;
        }

        Set<String> impactedSet = new HashSet<>(plan.getImpactedFiles());
        return allFiles.stream()
            .filter(f -> impactedSet.contains(f.getPath()) || impactedSet.contains(f.getName()))
            .collect(Collectors.toList());
    }

    public List<AnalysisFinding> mergeFindings(List<AnalysisFinding> newFindings, List<AnalysisFinding> cachedFindings) {
        Map<String, AnalysisFinding> merged = new LinkedHashMap<>();

        for (AnalysisFinding cached : cachedFindings) {
            String key = findingKey(cached);
            merged.put(key, cached);
        }

        for (AnalysisFinding newFinding : newFindings) {
            String key = findingKey(newFinding);
            merged.put(key, newFinding);
        }

        return new ArrayList<>(merged.values());
    }

    public Mono<Void> updateBaseline(String projectId, String commitHash, List<AnalysisFinding> allFindings) {
        String findingsHash = sha256(allFindings.stream()
            .map(this::findingKey)
            .sorted()
            .collect(Collectors.joining("|")));

        AnalysisBaseline newBaseline = AnalysisBaseline.builder()
            .id(UUID.randomUUID().toString())
            .projectId(projectId)
            .commitHash(commitHash)
            .findingsHash(findingsHash)
            .findings(allFindings)
            .createdAt(Instant.now().toString())
            .build();

        return baselineRepository.save(newBaseline)
            .then()
            .doOnSuccess(v -> log.info("Updated baseline for project {} at commit {}", projectId, commitHash))
            .doOnError(e -> log.error("Failed to update baseline for project {}: {}", projectId, e.getMessage()));
    }

    public Mono<Void> clearBaseline(String projectId) {
        return baselineRepository.findByProjectId(projectId)
            .flatMap(baselineRepository::delete)
            .then()
            .doOnSuccess(v -> log.info("Cleared baselines for project {}", projectId));
    }

    private String findingKey(AnalysisFinding finding) {
        return finding.getFile() + ":" + finding.getLine() + ":" + finding.getCategory() + ":" + finding.getMessage();
    }

    private String sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes());
            StringBuilder hex = new StringBuilder();
            for (byte b : hash) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (Exception e) {
            return String.valueOf(input.hashCode());
        }
    }

    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class IncrementalAnalysisPlan {
        private String projectId;
        private String currentCommit;
        private String baselineCommit;
        private boolean fullAnalysis;
        private List<String> changedFiles;
        private List<String> impactedFiles;
        private List<AnalysisFinding> cachedFindings;
    }
}
