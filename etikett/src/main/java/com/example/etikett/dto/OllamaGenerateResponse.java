package com.example.etikett.dto;

import lombok.Data;

@Data
public class OllamaGenerateResponse {

    private String response;
    private Boolean done;
    private String model;

}
