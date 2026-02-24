package com.example.etikett.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "kafka.topics")
public class KafkaTopicsProperties {

    private String input = "tickets-formatted";
    private String output = "tickets-labeled";
    private String dlq = "tickets-labeled-dlq";

}
