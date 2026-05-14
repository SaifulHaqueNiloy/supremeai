package com.supremeai.dto;

import lombok.Data;
import java.util.Map;

@Data
public class PubSubMessageEnvelope {
    private Message message;
    private String subscription;

    @Data
    public static class Message {
        private Map<String, String> attributes;
        private String data;
        private String messageId;
        private String publishTime;
    }
}
