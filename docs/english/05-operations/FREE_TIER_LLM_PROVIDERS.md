# SupremeAI 2.0 — Free Tier LLM Providers Guide

This guide compiles the API keys and endpoints for both our **active** zero-cost providers and our **recommended** expansions to maximize rate-limits and token quotas under a zero-cost architecture.

---

## 🔑 Active Core Providers

These providers are already integrated and configured inside our codebase and Continue workspace configurations.

### 1. Google Gemini (Google AI Studio)
* **Console URL:** https://aistudio.google.com/
* **Model Identifiers:** 
  * `gemini-1.5-flash` (Fast, high-rate limits)
  * `gemini-2.5-flash` (Balanced text/reasoning)
  * `gemini-3.5-flash` (Advanced logic and parsing)
* **Rate Limits (Free Tier):** 15 RPM (Requests Per Minute), 1 million TPM (Tokens Per Minute), 1,500 RPD (Requests Per Day).
* **Key Benefits:** Massive context window (up to 2 million tokens), excellent multimodal vision support, highly stable, and completely free developer keys.

### 2. Groq Cloud
* **Console URL:** https://console.groq.com/
* **Model Identifiers:**
  * `llama-3.3-70b-versatile` (Primary coding and reasoning model)
  * `llama-3.1-8b-instant` (Ultra-fast chat/completions)
* **Rate Limits (Free Tier):** Generous token and request quotas per minute, split dynamically based on global load.
* **Key Benefits:** Hardware-accelerated inference (extremely fast response times), perfect for rapid code autocomplete and fast chat replies.

### 3. OpenRouter
* **Console URL:** https://openrouter.ai/keys
* **Model Identifiers:**
  * `meta-llama/llama-3.3-70b-instruct` (Full instruction Llama 3.3)
  * *Supports fallback to various free models on OpenRouter (e.g. Mistral, Qwen)*
* **Rate Limits (Free Tier):** Subject to individual model constraints (many models are completely free with basic rate-limiting).
* **Key Benefits:** Single endpoint key providing access to hundreds of open-source models; automatically handles failovers to free models.

### 4. GitHub Models (Copilot / Developer Preview)
* **Console URL:** https://github.com/marketplace/models
* **Model Identifiers:**
  * `gpt-4o` (OpenAI flagship model)
  * `gpt-4o-mini` (Fast OpenAI lightweight model)
* **Rate Limits (Free Tier):** Basic rate-limits based on your GitHub Developer account level (resets dynamically).
* **Key Benefits:** Completely free access to OpenAI's flagship models without an OpenAI billing account. Useful for heavy vision or complex coding tasks.

---

## 🚀 Recommended Expansion Providers (Next Mission)

To increase our system's resiliency, we recommend signing up and generating API keys for these highly-optimized, free-tier platforms:

### 1. SambaNova Cloud
* **Console URL:** https://cloud.sambanova.ai/
* **Model Identifiers:**
  * `meta-llama/Llama-3.3-70B-Instruct`
  * `meta-llama/Llama-3.1-8B-Instruct`
  * `Qwen/Qwen2.5-Coder-32B-Instruct`
* **Rate Limits (Free Tier):** Highly generous RPM and TPM on dedicated hardware backends.
* **Key Benefits:** High speed, completely free during their developer promotion, and fully OpenAI-compatible.

### 2. Together AI
* **Console URL:** https://api.together.xyz/
* **Model Identifiers:**
  * `meta-llama/Llama-3.3-70b-instruct`
  * `deepseek-ai/DeepSeek-V3`
* **Free Tier Credit:** **$25.00 free credit** upon registration (no credit card required, verified by phone).
* **Key Benefits:** Fast inference speeds, stable platform, supports massive open-weight models.

### 3. Cerebras Cloud
* **Console URL:** https://cloud.cerebras.ai/
* **Model Identifiers:**
  * `llama-3.3-70b`
  * `llama-3.1-8b`
* **Rate Limits (Free Tier):** Extremely high speed (1000+ tokens/sec) under free developer tier.
* **Key Benefits:** World-record inference speeds; ideal for instantaneous autocomplete and code compilation tests.

### 4. Cohere AI
* **Console URL:** https://dashboard.cohere.com/
* **Model Identifiers:**
  * `command-r`
  * `command-r-plus`
* **Rate Limits (Free Tier):** Free Trial key (4 RPM limit).
* **Key Benefits:** Exceptional performance for Retrieval Augmented Generation (RAG), search tasks, and multilingual document translation.

### 5. Mistral AI (La Plateforme)
* **Console URL:** https://console.mistral.ai/
* **Model Identifiers:**
  * `codestral-latest` (Mistral's state-of-the-art coding model)
  * `mistral-large-latest` (Flagship reasoning model)
* **Free Tier Credit:** Free developer tier trial keys available upon registration.
* **Key Benefits:** Codestral is one of the best code completion models in the open ecosystem.

---

## 🔄 How to Integrate New Keys

When you obtain new API keys, follow these simple steps to add them to SupremeAI:

1. Add the keys to your local `.env` file (e.g. `SAMBANOVA_API_KEY="your-key"`).
2. Run the centralized sync script to propagate the keys to GitHub, Render, and Vercel:
   ```bash
   python scripts/sync_all_platforms_env.py --apply
   ```
3. Update the `multi_account_rotator.py` or `llm_gateway.py` to route through the new models.
