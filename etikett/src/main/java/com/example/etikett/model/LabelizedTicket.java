package com.example.etikett.model;

import lombok.Data;

@Data
public class LabelizedTicket {

    private FormattedTicket formattedTicket;
    private Category category;
    private Priority priority;
    private Type type;

}
