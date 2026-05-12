package com.supremeai.model;

import com.google.cloud.firestore.annotation.DocumentId;
import com.google.cloud.firestore.annotation.ServerTimestamp;
import org.springframework.data.annotation.Id;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * Generated application stored in Firestore.
 * Collection: "generated_apps"
 */
public class GeneratedApp {

    @DocumentId
    private String appId;

    private String userId;

    private String platform;  // WEB, IOS, ANDROID, DESKTOP

    private String language;  // SwiftUI, Kotlin, React, Tauri

    private String htmlContent;  // For web apps: complete HTML

    private Map<String, String> sourceFiles;  // filename → content for multi-file projects

    private String version;

    private String status;  // GENERATED, DEPLOYED, ERROR

    private String errorMessage;

    private byte[] screenshot;

    @ServerTimestamp
    private LocalDateTime createdAt;

    @ServerTimestamp
    private LocalDateTime updatedAt;

    public GeneratedApp() {}

    public GeneratedApp(String appId, String userId, String platform, String language) {
        this.appId = appId;
        this.userId = userId;
        this.platform = platform;
        this.language = language;
        this.version = "1.0.0";
        this.status = "GENERATED";
        this.createdAt = LocalDateTime.now();
    }

    public String getAppId() { return appId; }
    public void setAppId(String appId) { this.appId = appId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public String getPlatform() { return platform; }
    public void setPlatform(String platform) { this.platform = platform; }

    public String getLanguage() { return language; }
    public void setLanguage(String language) { this.language = language; }

    public String getHtmlContent() { return htmlContent; }
    public void setHtmlContent(String htmlContent) { this.htmlContent = htmlContent; }

    public Map<String, String> getSourceFiles() { return sourceFiles; }
    public void setSourceFiles(Map<String, String> sourceFiles) { this.sourceFiles = sourceFiles; }

    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }

    public byte[] getScreenshot() { return screenshot; }
    public void setScreenshot(byte[] screenshot) { this.screenshot = screenshot; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
