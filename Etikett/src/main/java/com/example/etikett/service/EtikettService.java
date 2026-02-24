package com.example.etikett.service;

import com.example.etikett.model.FormattedTicket;
import com.example.etikett.model.LabelizedTicket;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class EtikettService {

    private final OllamaClient ollamaClient;
    private final LlmLabelParser llmLabelParser;

    public EtikettService(OllamaClient ollamaClient, LlmLabelParser llmLabelParser) {
        this.ollamaClient = ollamaClient;
        this.llmLabelParser = llmLabelParser;
    }

    public ResponseEntity<LabelizedTicket> label(FormattedTicket formattedTicket) {
        log.info("Labeling ticket from '{}'", formattedTicket.getContact());

        String prompt = buildPrompt(formattedTicket);
        String llmText = ollamaClient.generate(prompt);
        LabelizedTicket labeled = llmLabelParser.parse(llmText, formattedTicket);

        log.info("Labeling complete: category={}, priority={}, type={}",
                labeled.getCategory(), labeled.getPriority(), labeled.getType());

        return ResponseEntity.ok(labeled);
    }

    private String buildPrompt(FormattedTicket ticket) {
        return String.format("""
                You are a ticket classifier. RESPOND ONLY WITH VALID JSON. NO EXPLANATIONS. NO EXTRA TEXT.

                Ticket:
                Contact: %s
                Origin: %s
                Date: %s
                Body: %s

                Valid category values: FRONT, BACK, INFRA, MOBILE
                Valid priority values: NULL, LOW, MEDIUM, HIGH
                Valid type values: FEATURE_REQUEST, BUG

                RESPOND WITH ONLY THIS JSON FORMAT, NOTHING ELSE:
                {"category":"BACK","priority":"MEDIUM","type":"BUG"}
                """,
                ticket.getContact(),
                ticket.getOrigin(),
                ticket.getDate(),
                ticket.getBody()
        );
    }
}
