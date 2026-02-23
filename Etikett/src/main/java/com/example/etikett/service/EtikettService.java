package com.example.etikett.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class EtikettService {

    public ResponseEntity<Map<String, String>> status() {
        log.info("Status check requested");
        Map<String, String> response = new HashMap<>();
        response.put("status", "up");
        response.put("service", "Etikett API");
        response.put("version", "1.0.0");
        log.debug("Status response prepared: {}", response);
        return ResponseEntity.ok(response);
    }

}
