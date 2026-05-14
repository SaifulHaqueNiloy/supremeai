# Production Dockerfile for SupremeAI Backend
# This Dockerfile expects a pre-built app.jar in the root directory
FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

# Create non-root user for security
RUN groupadd -r supremeai && useradd -r -g supremeai supremeai

# Create logs directory with proper ownership
RUN mkdir -p logs && chown supremeai:supremeai logs && chmod 750 logs

# Copy the pre-built JAR from the root
COPY app.jar app.jar

USER supremeai

ENV PORT=8080
ENV SPRING_PROFILES_ACTIVE=cloud
ENV JAVA_OPTS="-Xms512m -Xmx1g -XX:+UseG1GC --enable-preview"

EXPOSE 8080

# Use exec form for proper signal handling
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar app.jar"]