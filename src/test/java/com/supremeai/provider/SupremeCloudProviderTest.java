package com.supremeai.provider;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class SupremeCloudProviderTest {

    @Test
    public void testGetRequestUrl_Standard() {
        SupremeCloudProvider provider = new SupremeCloudProvider("key", "test_provider", "model", "https://api.example.com");
        assertEquals("https://api.example.com/v1/chat/completions", provider.getRequestUrl());
    }

    @Test
    public void testGetRequestUrl_TrailingSlash() {
        SupremeCloudProvider provider = new SupremeCloudProvider("key", "test_provider", "model", "https://api.example.com/");
        assertEquals("https://api.example.com/v1/chat/completions", provider.getRequestUrl());
    }

    @Test
    public void testGetRequestUrl_HfInference() {
        // Mock HF inference URL
        SupremeCloudProvider provider = new SupremeCloudProvider("key", "hf_test", "model", "https://api-inference.huggingface.co/models/test");
        assertEquals("https://api-inference.huggingface.co/models/test", provider.getRequestUrl());
    }

    @Test
    public void testGetCapabilities() {
        SupremeCloudProvider provider = new SupremeCloudProvider("key", "render_test", "model_x", "https://render.com");
        var caps = provider.getCapabilities();
        assertEquals("render_test", caps.get("name"));
        assertEquals("model_x", caps.get("model"));
        assertEquals("cloud-native", caps.get("type"));
    }
}
