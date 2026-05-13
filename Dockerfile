# Multi-stage Docker build for SupremeAI Spring Boot backend
# Stage 1: Build with Gradle
FROM gradle:8.10-jdk21 AS builder
WORKDIR /app
COPY --chown=gradle:gradle . .
RUN gradle bootJar --no-daemon --stacktrace

# Stage 2: Runtime image (Alpine JRE)
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

# Install gcloud CLI (required by SimulatorDeploymentService)
RUN apk add --no-cache \
    curl \
    bash \
    python3 \
    && curl -sSL https://sdk.cloud.google.com | bash \
    && ln -sf /root/google-cloud-sdk/bin/gcloud /usr/bin/gcloud \
    && gcloud --version

# Copy JAR
COPY --from=builder /app/build/libs/*.jar app.jar

# Expose Spring Boot default
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java -Dserver.port=${PORT:-8080} -jar app.jar"]
