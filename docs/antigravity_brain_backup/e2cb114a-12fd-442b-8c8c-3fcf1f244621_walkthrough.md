# Guardian Agent Implementation Walkthrough

This document summarizes the implementation of the **Guardian Agent**, which tracks codebase compliance against the rules defined in `agent_rules.json`.

## What Was Done

### 1. Guardian Agent Registration
We added a new configuration block for `guardian_expert` into our `backend/core/agent_registry.json`.
- **System Prompt**: Programmed to enforce codebase compliance based on `agent_rules.json`.
- **Assigned Tools**: `rules_parser`, `code_analyzer`, `ci_command_runner`.
- **Description**: Tracks user/system code and enforces architectural, security, and clean code rules.

### 2. Agent Execution Script
Created a standalone testing and execution script at [`scripts/run_guardian_agent.py`](file:///C:/Users/n/supremeai/supremeai_2.0/scripts/run_guardian_agent.py).
- **Initialization**: Leverages the newly updated `DynamicAgentFactory` to load the Guardian Agent profile from the `AgentRegistry`.
- **Rule Loading**: Automatically parses `agent_rules.json` to extract all `automatable: true` active rules (like `CLEAN-018`, `CORE-001`, `SEC-047`, etc.).
- **Code Analysis**: Acts as a bridge between the local code (e.g., `cost_guard_monitor.py` as a test case) and the unified `llm_gateway`, allowing the AI to scan the code explicitly for any rule violations.

> [!SUCCESS]
> The Guardian Agent is fully functional. It acts as a static analysis orchestrator powered by LLM, ready to be integrated into PR pipelines or automated checks to ensure absolute adherence to SupremeAI 2.0's coding standards.
