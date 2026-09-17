---
target_scope: supremeai_internal
# [V5 audit 2026-09-17] Legacy doc migrated to canonical governance schema; defaults are conservative (historical/derived role) — refine on next lifecycle review.
id: auto:vscode_lm_multi_model_ide_support_plan
subject: Integrate `vscode.lm` for In-built IDE Model Support
document_role: implementation
planning_authority: Architecture Governance / Planning Circle
status: historical

---

# Integrate `vscode.lm` for In-built IDE Model Support

This plan outlines the steps to allow the SupremeAI VS Code Extension to automatically detect and utilize free in-built AI models provided by the host IDE (such as Antigravity IDE or GitHub Copilot) via the official `vscode.lm` (Language Model) API.

## User Review Required
> [!IMPORTANT]
> The `vscode.lm` API is a relatively new feature in VS Code. To ensure compatibility, we will implement this with graceful degradation. If the user is on an older version of VS Code or no models are found, it will seamlessly fall back to your existing OpenRouter/Ollama logic. 

## Open Questions
> [!WARNING]  
> Are there specific model families you want to target (e.g., `vendor: 'copilot'`, `family: 'gemini'`) or should we just select the first available model that the IDE provides? My current plan is to ask for any available model (`vscode.lm.selectChatModels()`) and pick the first one to maximize compatibility. Let me know if you prefer a specific filtering logic.

## Proposed Changes

---

### SupremeAIService (Core Backend & Fallback Logic)

We will modify `SupremeAIService.ts` to introduce a new fallback layer. The routing order upon backend failure will become:
1. `vscode.lm` (Free IDE in-built models)
2. `Ollama / OpenRouter` (Configured API fallbacks)

#### [MODIFY] [SupremeAIService.ts](file:///f:/supremeai%20backup/tools/vscode-extension/src/services/SupremeAIService.ts)

**Modifications:**
1. **Add `tryIdeLanguageModelFallback`:**
   - Create a new method that attempts to fetch models using `vscode.lm.selectChatModels()`.
   - Convert the `message` string into a `vscode.LanguageModelChatMessage.User(message)`.
   - Send the request to the model and return the generated text.

2. **Add `streamIdeLanguageModelFallback`:**
   - Create a method for handling streaming responses.
   - Iterate over the `response.text` async iterable provided by `vscode.lm` and fire the `onToken` callback for real-time streaming in the chat UI.

3. **Update `sendChatMessage`:**
   - Modify the `catch` block. First, try `tryIdeLanguageModelFallback`. If it throws an error (e.g., no models found, or API not available), catch it and immediately invoke the existing `tryFreeModelFallback`.

4. **Update `streamChatCompletion`:**
   - Modify the `catch` block to try `streamIdeLanguageModelFallback` first, and if that fails, proceed to `tryFreeModelFallback`.

## Verification Plan

### Automated Tests
- Run `npm run compile` and `npm run lint` to ensure TypeScript compilation passes and there are no type errors with the `vscode` namespace usage.

### Manual Verification
- Test inside Antigravity IDE (or standard VS Code with GitHub Copilot installed).
- Temporarily change the `backendUrl` to an invalid URL to simulate a server failure.
- Trigger a chat message in SupremeAI.
- Verify that the chat resolves successfully using the IDE's built-in model instead of immediately falling back to OpenRouter.