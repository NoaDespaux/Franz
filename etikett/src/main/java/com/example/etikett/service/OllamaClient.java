package com.example.etikett.service;

import com.example.etikett.config.OllamaProperties;
import com.example.etikett.dto.OllamaGenerateRequest;
import com.example.etikett.dto.OllamaGenerateResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Component
public class OllamaClient {

    private final RestClient restClient;
    private final OllamaProperties properties;

    public OllamaClient(RestClient.Builder restClientBuilder, OllamaProperties properties) {
        this.restClient = restClientBuilder.baseUrl(properties.getBaseUrl()).build();
        this.properties = properties;
    }

    public String generate(String prompt) {
        Map<String, Object> options = new HashMap<>();
        options.put("temperature", properties.getTemperature());
        options.put("num_predict", properties.getMaxTokens());

        OllamaGenerateRequest request = new OllamaGenerateRequest(
                properties.getModel(),
                prompt,
                false,
                options
        );

        log.debug("Calling Ollama at {} with model {}", properties.getBaseUrl(), properties.getModel());

        OllamaGenerateResponse response = restClient.post()
                .uri("/api/generate")
                .body(request)
                .retrieve()
                .body(OllamaGenerateResponse.class);

        if (response == null || response.getResponse() == null) {
            throw new IllegalStateException("Ollama returned an empty response");
        }

        return response.getResponse();
    }
}

