package com.example.etikett.controller;

import com.example.etikett.service.EtikettService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/etikett")
@Tag(name = "Etikett Controller", description = "Basic controller for Etikett operations")
public class EtikettController {

    private final EtikettService etikettService;

    public EtikettController(EtikettService etikettService) {
        this.etikettService = etikettService;
    }

    @GetMapping("/status")
    @Operation(summary = "Check API status", description = "Returns the current API status")
    public ResponseEntity<Map<String, String>> status() {
        return etikettService.status();
    }

}
