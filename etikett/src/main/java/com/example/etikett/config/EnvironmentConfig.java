package com.example.etikett.config;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;

@Slf4j
@Configuration
public class EnvironmentConfig {

    private final Environment env;

    @Autowired
    public EnvironmentConfig(Environment env) {
        this.env = env;
    }

    @PostConstruct
    public void verifyEnvironmentVariables() {
        log.info("Validating required environment variables...");

        validateVariable("OLLAMA_BASE_URL");
        validateVariable("OLLAMA_MODEL");
        validateVariable("OLLAMA_TEMPERATURE");
        validateVariable("OLLAMA_MAX_TOKENS");
        validateVariable("KAFKA_BOOTSTRAP_SERVERS");
        validateVariable("KAFKA_CONSUMER_GROUP_ID");
        validateVariable("KAFKA_CONSUMER_AUTO_OFFSET_RESET");
        validateVariable("KAFKA_TOPIC_INPUT");
        validateVariable("KAFKA_TOPIC_OUTPUT");
        validateVariable("KAFKA_TOPIC_DLQ");

        log.info("✓ All required environment variables are configured");
    }

    private void validateVariable(String variableName) {
        String value = env.getProperty(variableName);
        if (value == null || value.trim().isEmpty()) {
            log.error("Environment variable ({}) is not set!", variableName);
            throw new IllegalStateException("Required environment variable is not configured: " + variableName);
        }
    }

}
