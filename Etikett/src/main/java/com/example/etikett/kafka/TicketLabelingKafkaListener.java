package com.example.etikett.kafka;

import com.example.etikett.config.KafkaTopicsProperties;
import com.example.etikett.model.FormattedTicket;
import com.example.etikett.model.LabelizedTicket;
import com.example.etikett.service.EtikettService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class TicketLabelingKafkaListener {

    private final EtikettService etikettService;
    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final KafkaTopicsProperties topicsProperties;
    private final ObjectMapper objectMapper;

    public TicketLabelingKafkaListener(
            EtikettService etikettService,
            KafkaTemplate<String, Object> kafkaTemplate,
            KafkaTopicsProperties topicsProperties) {
        this.etikettService = etikettService;
        this.kafkaTemplate = kafkaTemplate;
        this.topicsProperties = topicsProperties;
        this.objectMapper = new ObjectMapper();
        log.info("TicketLabelingKafkaListener initialized, listening on topic: {}", topicsProperties.getInput());
    }

    @KafkaListener(topics = "${kafka.topics.input}", groupId = "${spring.kafka.consumer.group-id}")
    public void processFormattedTicket(FormattedTicket formattedTicket) {
        log.info("Received FormattedTicket from Kafka: contact={}, origin={}, bodyLength={}",
                formattedTicket.getContact(), formattedTicket.getOrigin(),
                formattedTicket.getBody() != null ? formattedTicket.getBody().length() : 0);

        try {
            // Validate ticket body has sufficient content for reliable labeling
            if (!isValidTicketBody(formattedTicket.getBody())) {
                log.warn("Ticket body too short or invalid from {}: '{}' (length: {})",
                        formattedTicket.getContact(),
                        formattedTicket.getBody(),
                        formattedTicket.getBody() != null ? formattedTicket.getBody().length() : 0);
                sendToErrorDlq(formattedTicket,
                        "Ticket body too short or invalid for reliable classification");
                return;
            }

            // Use the existing labeling service
            LabelizedTicket labelizedTicket = etikettService.label(formattedTicket)
                    .getBody();

            if (labelizedTicket != null) {
                // Log full labeled payload for local verification
                log.info("Labeled ticket payload: {}", labelizedTicket);
                // Send result to output topic
                kafkaTemplate.send(topicsProperties.getOutput(),
                        formattedTicket.getContact(),
                        labelizedTicket);

                log.info("Published labeled ticket to Kafka topic '{}': category={}, priority={}, type={}",
                        topicsProperties.getOutput(),
                        labelizedTicket.getCategory(),
                        labelizedTicket.getPriority(),
                        labelizedTicket.getType());
            } else {
                log.warn("Labeling service returned null for ticket from: {}", formattedTicket.getContact());
                sendToErrorDlq(formattedTicket, "Labeling service returned null");
            }

        } catch (Exception e) {
            log.error("Error processing ticket from Kafka: {}", formattedTicket.getContact(), e);
            sendToErrorDlq(formattedTicket, e.getMessage());
        }
    }

    /**
     * Validates that the ticket body has sufficient content for reliable LLM classification.
     * Messages that are too short may result in unreliable categorization.
     *
     * @param body the ticket body to validate
     * @return true if the body is valid for classification, false otherwise
     */
    private boolean isValidTicketBody(String body) {
        if (body == null || body.isBlank()) {
            return false;
        }

        String trimmed = body.trim();

        // Minimum length threshold for reliable classification
        // Single character or very short messages are unreliable
        int minLength = 10;
        return trimmed.length() >= minLength;
    }

    /**
     * Sends a ticket to the DLQ topic when labeling cannot be performed reliably.
     *
     * @param formattedTicket the original ticket that failed processing
     * @param errorReason the reason why the ticket was sent to DLQ
     */
    private void sendToErrorDlq(FormattedTicket formattedTicket, String errorReason) {
        try {
            String dlqTopic = topicsProperties.getDlq();
            if (dlqTopic != null && !dlqTopic.isBlank()) {
                // Create error payload with original ticket and error details
                String errorPayload = String.format(
                        "{\"originalTicket\": %s, \"error\": \"%s\", \"timestamp\": %d}",
                        convertToJson(formattedTicket),
                        errorReason != null ? errorReason.replace("\"", "\\\"") : "Unknown error",
                        System.currentTimeMillis()
                );

                kafkaTemplate.send(dlqTopic,
                        formattedTicket.getContact(),
                        errorPayload);

                log.info("Sent error payload to DLQ topic '{}' for ticket from: {} (reason: {})",
                        dlqTopic, formattedTicket.getContact(), errorReason);
            }
        } catch (Exception dlqError) {
            log.error("Failed to send error to DLQ topic: {}", dlqError.getMessage(), dlqError);
        }
    }

    private String convertToJson(Object obj) throws Exception {
        return objectMapper.writeValueAsString(obj);
    }
}
