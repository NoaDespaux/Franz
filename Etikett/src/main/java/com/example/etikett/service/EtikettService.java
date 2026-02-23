package com.example.etikett.service;

import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class EtikettService {

    public ResponseEntity<Map<String, String>> status() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "up");
        response.put("service", "Etikett API");
        response.put("version", "1.0.0");
        return ResponseEntity.ok(response);
    }

}
