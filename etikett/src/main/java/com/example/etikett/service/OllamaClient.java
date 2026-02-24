package com.example.etikett.service;

import com.example.etikett.dto.OllamaGenerateRequest;
import com.example.etikett.dto.OllamaGenerateResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Component
public class OllamaClient {

    private final RestClient restClient;

    @Value("${ollama.base-url}")
    private String baseUrl;

    @Value("${ollama.model}")
    private String model;

    @Value("${ollama.temperature}")
    private Double temperature;

    @Value("${ollama.max-tokens}")
    private Integer maxTokens;

    public OllamaClient(RestClient.Builder restClientBuilder, @Value("${ollama.base-url}") String baseUrl) {
        this.restClient = restClientBuilder.baseUrl(baseUrl).build();
    }

    public String generate(String prompt) {
        Map<String, Object> options = new HashMap<>();
        options.put("temperature", temperature);
        options.put("num_predict", maxTokens);

        OllamaGenerateRequest request = new OllamaGenerateRequest(
                model,
                prompt,
                false,
                options
        );

        log.debug("Calling Ollama at {} with model {}", baseUrl, model);

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
