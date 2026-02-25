package com.example.etikett.dto;

import com.example.etikett.model.FormattedTicket;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ErrorPayload {
    private FormattedTicket originalTicket;
    private String error;
    private long timestamp;
}

