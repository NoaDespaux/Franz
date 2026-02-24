package com.example.etikett.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class OllamaGenerateRequest {

    private String model;
    private String prompt;
    private Boolean stream;
    private Map<String, Object> options;

}
