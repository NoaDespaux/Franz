package com.example.etikett.service;

import com.example.etikett.model.Category;
import com.example.etikett.model.FormattedTicket;
import com.example.etikett.model.LabelizedTicket;
import com.example.etikett.model.Priority;
import com.example.etikett.model.Type;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class LlmLabelParser {

    private final ObjectMapper objectMapper;

    public LlmLabelParser(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public LabelizedTicket parse(String llmText, FormattedTicket formattedTicket) {
        try {
            log.debug("Raw LLM response (first 500 chars): {}",
                    llmText.length() > 500 ? llmText.substring(0, 500) + "..." : llmText);

            String json = extractJson(llmText);
            log.debug("Extracted JSON: {}", json);

            JsonNode node = objectMapper.readTree(json);

            LabelizedTicket labelizedTicket = new LabelizedTicket();
            labelizedTicket.setFormattedTicket(formattedTicket);
            labelizedTicket.setCategory(parseEnum(Category.class, node, "category"));
            labelizedTicket.setPriority(parseEnum(Priority.class, node, "priority"));
            labelizedTicket.setType(parseEnum(Type.class, node, "type"));

            return labelizedTicket;
        } catch (Exception e) {
            log.error("Failed to parse LLM response: {}", llmText, e);
            throw new IllegalStateException("Unable to parse LLM response: " + e.getMessage(), e);
        }
    }

    String extractJson(String text) {
        if (text == null || text.trim().isEmpty()) {
            throw new IllegalStateException("Empty LLM response");
        }

        String trimmed = text.trim();

        // Remove markdown code blocks if present
        if (trimmed.startsWith("```json")) {
            trimmed = trimmed.substring(7);
        } else if (trimmed.startsWith("```")) {
            trimmed = trimmed.substring(3);
        }
        if (trimmed.endsWith("```")) {
            trimmed = trimmed.substring(0, trimmed.length() - 3);
        }

        // Find JSON object boundaries - most robust approach
        int start = trimmed.indexOf('{');
        int end = trimmed.lastIndexOf('}') + 1;

        if (start < 0 || end <= start) {
            throw new IllegalStateException("No JSON object found in LLM response: " + text);
        }

        String json = trimmed.substring(start, end).trim();

        // Validate it's valid JSON by checking for required fields
        if (!json.contains("\"category\"") && !json.contains("\"priority\"") && !json.contains("\"type\"")) {
            throw new IllegalStateException("Extracted text does not appear to be valid classification JSON");
        }

        return json;
    }

    private <E extends Enum<E>> E parseEnum(Class<E> enumType, JsonNode node, String field) {
        if (node == null || !node.has(field)) {
            throw new IllegalStateException("Missing required field '" + field + "' in LLM response");
        }

        String value = node.get(field).asText("").trim().toUpperCase();
        if (value.isEmpty()) {
            throw new IllegalStateException("Empty value for required field '" + field + "' in LLM response");
        }

        try {
            return Enum.valueOf(enumType, value);
        } catch (IllegalArgumentException ex) {
            throw new IllegalStateException("Invalid value '" + value + "' for field '" + field +
                    "'. Expected one of: " + String.join(", ", getEnumNames(enumType)), ex);
        }
    }

    private <E extends Enum<E>> String[] getEnumNames(Class<E> enumType) {
        E[] constants = enumType.getEnumConstants();
        String[] names = new String[constants.length];
        for (int i = 0; i < constants.length; i++) {
            names[i] = constants[i].name();
        }
        return names;
    }
}
