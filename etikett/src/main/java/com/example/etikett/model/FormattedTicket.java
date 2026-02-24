package com.example.etikett.model;

import lombok.Data;

import java.util.Date;

@Data
public class FormattedTicket {

    private String contact;
    private String origin;
    private Date date;
    private String body;

}
