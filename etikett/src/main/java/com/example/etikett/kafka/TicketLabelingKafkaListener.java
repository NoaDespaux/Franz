package com.example.etikett.kafka;

import com.example.etikett.dto.ErrorPayload;
import com.example.etikett.model.FormattedTicket;
import com.example.etikett.model.LabelizedTicket;
import com.example.etikett.service.EtikettService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class TicketLabelingKafkaListener {

    private final EtikettService etikettService;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Value("${kafka.topics.input}")
    private String inputTopic;

    @Value("${kafka.topics.output}")
    private String outputTopic;

    @Value("${kafka.topics.dlq}")
    private String dlqTopic;

    public TicketLabelingKafkaListener(
            EtikettService etikettService,
            KafkaTemplate<String, Object> kafkaTemplate) {
        this.etikettService = etikettService;
        this.kafkaTemplate = kafkaTemplate;
    }

    @org.springframework.context.event.EventListener(org.springframework.context.event.ContextRefreshedEvent.class)
    public void logInitialization() {
        log.info("TicketLabelingKafkaListener initialized, listening on topic: {}", inputTopic);
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
                kafkaTemplate.send(outputTopic,
                        formattedTicket.getContact(),
                        labelizedTicket);

                log.info("Published labeled ticket to Kafka topic '{}': category={}, priority={}, type={}",
                        outputTopic,
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
            if (dlqTopic != null && !dlqTopic.isBlank()) {
                // Create error payload with original ticket and error details
                ErrorPayload errorPayload = new ErrorPayload(
                        formattedTicket,
                        errorReason != null ? errorReason : "Unknown error",
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
}
