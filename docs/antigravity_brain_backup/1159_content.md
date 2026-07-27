Title: Live Content

Description: Fetched live

Source: https://launchdarkly.com/docs/home/agentcontrol/agentcontrol-prompt.md

---

> For clean Markdown of any page, append .md to the page URL.
> For a complete documentation index, see https://launchdarkly.com/docs/llms.txt.
> For AI client integration (Claude Code, Cursor, etc.), connect to the MCP server at https://launchdarkly.com/docs/_mcp/server.

# AgentControl onboarding prompt

> A prompt you can give to your coding assistant to set up LaunchDarkly AgentControl in your application.

> For clean Markdown of any page, append .md to the page URL.
> For a complete documentation index, see [https://launchdarkly.com/docs/llms.txt](https://launchdarkly.com/docs/llms.txt).
> For full documentation content, see [https://launchdarkly.com/docs/llms-full.txt](https://launchdarkly.com/docs/llms-full.txt). This file is very large and may time out.
> For AI client integration (Claude Code, Cursor, etc.), connect to the MCP server at [https://launchdarkly.com/docs/\_mcp/server](https://launchdarkly.com/docs/_mcp/server).

# LaunchDarkly AgentControl — Agent Onboarding Prompt

You are helping a developer wire up **LaunchDarkly AgentControl** into their application.
Follow the phases below. **Stop at the end of each phase and wait for user confirmation before continuing.**

> **Naming note for the agent.** AgentControl is the LaunchDarkly product for managing **configs** (model + prompt + parameters + tools, served from LaunchDarkly at runtime to drive your AI features). The product was previously called *AI Configs*; the user-facing terminology is now **AgentControl** (product) and **configs** (the things you create inside it).
>
> **Many technical identifiers still use the old `ai-config` / `ai_config` / `AI` prefix and have not been renamed.** This is intentional — the SDK packages, classes, MCP tool names, environment variable names, and documentation URLs ship under the legacy names and changing them in code without an SDK release would break the user's app. Keep using:
>
> * SDK package names: `launchdarkly-server-sdk-ai`, `@launchdarkly/server-sdk-ai`, `@launchdarkly/server-sdk-ai-openai`
> * SDK classes / functions: `LDAIClient`, `AICompletionConfigDefault`, `AIAgentConfigDefault`, `completion_config()`, `agent_config()`, `create_model()`, `create_judge()`
> * MCP tool names: `setup-ai-config`, `create-ai-config-variation`, `update-ai-config-variation`, `create-ai-tool`, `list-ai-configs`, `get-ai-config`, `update-ai-config-rollout`, etc.
> * Environment variables: `LAUNCHDARKLY_AI_CONFIG_KEY`, `LAUNCHDARKLY_AI_JUDGE_KEY`
> * Documentation URLs: `https://docs.launchdarkly.com/home/ai-configs/...`, `https://docs.launchdarkly.com/sdk/ai/...`
>
> Use **AgentControl** and **config / configs** in *prose, headings, status messages, and anything you say to the user*. Use the legacy `ai-config` identifiers in *code, MCP calls, env vars, and URLs*. If the user asks why, explain that the rename is rolling out across the product surface and the identifiers will update on their normal release cadence.

## Core principles

* **Detect before asking** — infer what you can from the codebase; ask only when ambiguous
* **Inspect before mutating** — understand the codebase before changing anything
* **Do not change business logic** — the LaunchDarkly integration is purely additive
* **Wrap, don't replace** — keep existing agent code intact; wrap it with the LaunchDarkly AI SDK to pull model config and instructions from LaunchDarkly at runtime
* **Follow existing code style** and project conventions
* **Keep output concise** — do not generate extra documentation or summary files
* **Ask before changing non-LaunchDarkly dependencies** — installing the LaunchDarkly AI SDK packages named in this prompt is in-scope. **Anything else** — upgrading existing packages to resolve peer-dependency warnings, downgrading the user's framework version, running `npm audit fix`, bumping `react`/`node`/etc. — requires explicit user approval before you run the command or edit the manifest. If the install reports peer conflicts, surface the exact error, propose the minimal change, and wait for the user to confirm before proceeding. The user's existing dependency versions may be pinned for reasons you cannot see (downstream apps, internal compatibility constraints, governance policies); silently bumping them is a high-cost mistake even when it makes the build pass.
* **Treat SDK keys and provider keys as last resort** — never fetch, write, or paste real keys without explicit user consent. The structured consent question in [Phase 2 Step 3](#3-set-up-credentials) is mandatory before writing anything to `.env` or any other secret store. Some users keep `.env` under tight controls (CI-only, secrets manager, encrypted vault) and an agent silently dropping a key into it is a security incident, not a convenience.
* **Prefer MCP over the UI when MCP can do the job** — when the LaunchDarkly MCP servers are connected, use them for any operation they support so the user stays inside the agent context instead of bouncing to the UI. Sending the user to the UI for something the agent could have done in one MCP call is a worse experience and a missed opportunity to demonstrate the platform. **Discover available tools dynamically:** at the start of any LaunchDarkly operation, list the tools exposed by both MCP servers and treat that live list as the source of truth — the [MCP capability map](#mcp-capability-map) below is a quick reference but it will go stale as new tools ship. If an MCP call fails, fall back immediately to the UI/REST steps without interrupting flow.

### Reference links

* **AgentControl quickstart:** [https://docs.launchdarkly.com/home/ai-configs/quickstart](https://docs.launchdarkly.com/home/ai-configs/quickstart)
* **AI SDKs overview:** [https://docs.launchdarkly.com/sdk/ai](https://docs.launchdarkly.com/sdk/ai)
* **Python AI SDK reference:** [https://docs.launchdarkly.com/sdk/ai/python](https://docs.launchdarkly.com/sdk/ai/python)
* **Node.js AI SDK reference:** [https://docs.launchdarkly.com/sdk/ai/nodejs](https://docs.launchdarkly.com/sdk/ai/nodejs)
* **Integration guides:** [https://docs.launchdarkly.com/guides/ai-configs](https://docs.launchdarkly.com/guides/ai-configs)
* **Python observability reference:** [https://docs.launchdarkly.com/sdk/observability/python](https://docs.launchdarkly.com/sdk/observability/python)
* **Node.js observability reference:** [https://docs.launchdarkly.com/sdk/observability/nodejs](https://docs.launchdarkly.com/sdk/observability/nodejs)
* **Python sample app:** [https://github.com/launchdarkly/hello-python-ai](https://github.com/launchdarkly/hello-python-ai)
* **Node.js sample apps:** [https://github.com/launchdarkly/js-core/tree/main/packages/sdk/server-ai/examples](https://github.com/launchdarkly/js-core/tree/main/packages/sdk/server-ai/examples)
* **Alpha SDKs (.NET, Go, Ruby):** [https://docs.launchdarkly.com/sdk/ai](https://docs.launchdarkly.com/sdk/ai)
* **LaunchDarkly REST API (AgentControl):** [https://apidocs.launchdarkly.com/tag/AI-configs](https://apidocs.launchdarkly.com/tag/AI-configs)

### LaunchDarkly MCP servers

Two MCP servers can automate LaunchDarkly operations from within the agent session. The tool surface is **expanding rapidly** — treat the live MCP tool list as the source of truth and the table below as a quick reference, not a hardcoded gap list.

| Server                              | What it covers                                                                                                                                                       |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **LaunchDarkly AgentControl**       | Configs, variations (including judge attachment), tools, prompt snippets, agent graphs, datasets, evaluations, playgrounds, targeting, guarded rollouts, experiments |
| **LaunchDarkly Feature Management** | Projects and environments (SDK keys), flag-level rollouts and targeting, approval requests, member invites                                                           |

#### Discover available MCP tools at session start

Before relying on the capability map below, **list the available MCP tools** for both servers (most MCP clients expose `tools/list` or an equivalent). Treat the live list as the source of truth — new tools ship frequently and the table below will go stale. If a task appears in the live tool list but not in this table, you can still use it. If a task in this table is no longer in the tool list, fall back to the UI for that operation.

A quick probe at the start of any LaunchDarkly operation:

1. List tools on the AgentControl MCP server.
2. List tools on the Feature Management MCP server.
3. If both lists return successfully, prefer MCP for any task they cover. If either probe fails (not installed, auth error, network), fall back to the UI/REST API for that scope without interrupting the user.

**`modelConfigKey` format** — required by `setup-ai-config` and `create-ai-config-variation`. Use `"Provider.model-id"` exactly. **Anthropic is the in-app onboarding default** (pre-selected, listed first in the UI); users who supply an OpenAI key instead need their model corrected — see the troubleshooting table.

| Provider                         | `modelConfigKey` examples                                                                |
| -------------------------------- | ---------------------------------------------------------------------------------------- |
| Anthropic *(onboarding default)* | `Anthropic.claude-sonnet-4-6`, `Anthropic.claude-opus-4-6`, `Anthropic.claude-haiku-4-5` |
| OpenAI                           | `OpenAI.gpt-5.4`, `OpenAI.gpt-4.1`, `OpenAI.o4-mini`                                     |
| Google Gemini                    | `GoogleAI.gemini-2.0-flash`, `GoogleAI.gemini-2.5-pro`                                   |
| AWS Bedrock                      | `AWSBedrock.anthropic.claude-sonnet-4-6`                                                 |

#### MCP capability map

Use this table as a starting reference. **The live `tools/list` output overrides this table.** When MCP is connected, prefer it for any operation it covers; fall back to the UI only when MCP is unavailable or a call fails.

| Task                                                                    | MCP tool(s)                                                                                                             |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Create config + first variation                                         | `setup-ai-config`                                                                                                       |
| List, get, update, or delete configs                                    | `list-ai-configs`, `get-ai-config`, `update-ai-config`, `delete-ai-config`                                              |
| Add, edit, clone, or delete a variation                                 | `create-ai-config-variation`, `update-ai-config-variation`, `clone-ai-config-variation`, `delete-ai-config-variation`   |
| Change the model on a variation (e.g., wrong provider after onboarding) | `update-ai-config-variation` (set `modelConfigKey` and `modelName`)                                                     |
| Attach or detach judges on a variation                                  | `create-ai-config-variation` / `update-ai-config-variation` (`judgeConfiguration` field)                                |
| Create, list, or get a tool definition                                  | `create-ai-tool`, `list-ai-tools`, `get-ai-tool`                                                                        |
| Attach tools to a variation                                             | `update-ai-config-variation` (`tools` field)                                                                            |
| Manage prompt snippets (reusable prompt blocks shared across configs)   | `list-prompt-snippets`, `get-prompt-snippet`, `create-prompt-snippet`, `update-prompt-snippet`, `delete-prompt-snippet` |
| Manage agent graphs (multi-agent topology)                              | `list-agent-graphs`, `get-agent-graph`, `create-agent-graph`, `update-agent-graph`, `delete-agent-graph`                |
| Manage datasets (input/output pairs for evaluation)                     | `list-datasets`, `get-dataset`, `create-dataset`, `delete-dataset`                                                      |
| Manage and run offline evaluations                                      | `list-evaluations`, `get-evaluation`, `create-evaluation`, `run-evaluation`, `get-evaluation-run-summary`               |
| Manage playgrounds (compare prompts/models programmatically)            | `list-playgrounds`, `get-playground`, `create-playground`, `update-playground`                                          |
| Manage experiments (A/B test variations)                                | `list-experiments`, `get-experiment`, `create-experiment`, `update-experiment`, `start-experiment-iteration`            |
| Start or stop a guarded rollout (V2 measured rollout on fallthrough)    | `start-guarded-rollout`, `stop-guarded-rollout`                                                                         |
| Set the default targeting rule (which variation is served)              | `update-ai-config-rollout`, `update-ai-config-targeting-rules`, `update-rollout`, `update-targeting-rules`              |
| Toggle the config on/off                                                | `toggle-flag`                                                                                                           |
| Get an SDK key, project, or environments                                | `get-project` (Feature Management MCP)                                                                                  |
| Submit or apply an approval request for a change                        | `create-approval-request`, `apply-approval-request`                                                                     |
| Invite team members by email (with optional role assignment)            | `invite-members`                                                                                                        |

**Operations that may still be UI-only** (verify against the live `tools/list` before assuming):

* **LLM Playground** as an interactive browser experience (the `*-playground` MCP tools cover the data model but the side-by-side interactive comparison UI is browser-only).
* **Account-level approval settings** (the *configuration* of when approvals are required — distinct from submitting approval requests).
* Any operation not present in the live `tools/list` for either server.

**Rule:** if a task is covered by a live MCP tool, do it via MCP and tell the user what you did — do not send them to the UI for something the agent can complete in one call. If MCP is not connected, or a specific tool isn't listed, fall back to the UI cleanly without interrupting flow.

***

## PHASE 0: DETERMINE STARTING POINT

Before scanning for frameworks, determine whether the user has an existing app to instrument.

### Check for existing app signals

Scan for:

* Source files with AI model calls (`.py`, `.ts`, `.js`)
* Package manifests — `package.json`, `pyproject.toml`, `requirements.txt`, `Pipfile`
* Imports of AI libraries (OpenAI, Anthropic, LangChain, Bedrock, Gemini, etc.)

### Decision logic

**If an existing app is detected:**
State what you found concisely (e.g., "I see a Python + LangChain project here").
Then confirm: "I'll integrate LaunchDarkly AgentControl into this app — shall I proceed with a quick analysis?"
→ Proceed to **Phase 1**.

**If no app is detected** (empty directory, no source files, or user says they haven't built their AI app yet):
Present this choice:

> "I don't see an existing AI application here. Would you like to:
>
> 1. **Use a sample app** — the fastest way to see LaunchDarkly AgentControl in action, no existing code needed
> 2. **Integrate into an app you're building** — I'll guide you through setup as you build"

→ If they choose **sample app**, follow the **Sample App Path** section below, then stop.
→ If they choose **option 2**, direct them to the quickstart ([https://docs.launchdarkly.com/home/ai-configs/quickstart](https://docs.launchdarkly.com/home/ai-configs/quickstart)) and offer to return once they have AI calls in place.

***

## SAMPLE APP PATH

For users who want to explore LaunchDarkly AgentControl using a ready-made app.
Walk the user through these steps; do not skip to Phase 1.

### Python sample app

**Repo:** [https://github.com/launchdarkly/hello-python-ai](https://github.com/launchdarkly/hello-python-ai)\
**Requirements:** Python 3.10+, [Poetry](https://python-poetry.org/)

If Poetry is not installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
# Then restart your shell or run:
export PATH="$HOME/.local/bin:$PATH"
```

```bash
git clone https://github.com/launchdarkly/hello-python-ai
cd hello-python-ai
```

**Step 1 — Set credentials** (create a `.env` or export directly):

```bash
export LAUNCHDARKLY_SDK_KEY="sdk-..."              # Account settings > Environments in LaunchDarkly UI
export LAUNCHDARKLY_AI_CONFIG_KEY="sample-ai-config"
export OPENAI_API_KEY="sk-..."                     # Or use another provider below
```

**Step 2 — Install and run** (choose one provider):

| Provider                               | Install                           | Extra env var         | Run command                             |
| -------------------------------------- | --------------------------------- | --------------------- | --------------------------------------- |
| OpenAI + observability *(recommended)* | `poetry install -E observability` | `OPENAI_API_KEY`      | `poetry run chat-observability-example` |
| OpenAI (basic)                         | `poetry install -E openai`        | `OPENAI_API_KEY`      | `poetry run openai-example`             |
| LangChain (multi-provider)             | `poetry install -E langchain`     | `OPENAI_API_KEY`      | `poetry run langchain-example`          |
| LangGraph (agent)                      | `poetry install -E langgraph`     | `OPENAI_API_KEY`      | `poetry run langgraph-agent-example`    |
| AWS Bedrock                            | `poetry install -E bedrock`       | *(boto3 auto-detect)* | `poetry run bedrock-example`            |
| Gemini                                 | `poetry install -E gemini`        | `GOOGLE_API_KEY`      | `poetry run gemini-example`             |

**Step 3 — Confirm connection**

After running the example and triggering at least one AI call, return to the LaunchDarkly UI. The onboarding panel will flip to **Connected**. You're done.

***

### Node.js / TypeScript sample apps

**Repo:** [https://github.com/launchdarkly/js-core/tree/main/packages/sdk/server-ai/examples](https://github.com/launchdarkly/js-core/tree/main/packages/sdk/server-ai/examples)

```bash
git clone https://github.com/launchdarkly/js-core
cd js-core/packages/sdk/server-ai/examples/chat-observability   # recommended: full observability support
npm install
```

Other available examples: `openai`, `bedrock`, `tracked-chat`, `chat-judge`, `vercel-ai`, `agent-graph-traversal`. Swap the folder name in the `cd` command to use a different one.

Set `LAUNCHDARKLY_SDK_KEY`, `LAUNCHDARKLY_AI_CONFIG_KEY`, and the provider API key, then follow the `README.md` in the chosen example folder.

***

## PHASE 1: ANALYSIS (read-only)

Scan the codebase and identify the developer's stack. **Do not write any code or create any files during this phase.**

### Language gate — check this first

Identify the primary language before proceeding. **Python and Node.js/TypeScript are the primary AI SDK languages** with full feature support, including observability, all framework integrations, and active development.

**If the project is Go, .NET (C#), or Ruby:**

> "LaunchDarkly has an alpha AI SDK for \[Go/.NET/Ruby] — you can get started with AgentControl, though it currently receives new features at a slower pace than the Python and Node.js SDKs, and does not yet have an observability plugin.
>
> * Go AI SDK: [https://docs.launchdarkly.com/sdk/ai/go](https://docs.launchdarkly.com/sdk/ai/go)
> * .NET AI SDK: [https://docs.launchdarkly.com/sdk/ai/dotnet](https://docs.launchdarkly.com/sdk/ai/dotnet)
> * Ruby AI SDK: [https://docs.launchdarkly.com/sdk/ai/ruby](https://docs.launchdarkly.com/sdk/ai/ruby)
>
> Follow the quickstart for your language: [https://docs.launchdarkly.com/home/ai-configs/quickstart](https://docs.launchdarkly.com/home/ai-configs/quickstart)
> Would you like to proceed with the alpha SDK, or switch to Python or Node.js for the full experience?"

**If the project uses a language with no AI SDK** (Java, Rust, PHP, etc.):

> "LaunchDarkly's AI SDKs currently support Python, Node.js, Go, .NET, and Ruby.
> For other languages, you can call the LaunchDarkly REST API directly or use a server-side SDK to evaluate flags. See [https://docs.launchdarkly.com/sdk](https://docs.launchdarkly.com/sdk) for all SDKs."

**If the project is Python or TypeScript/JavaScript:** proceed with the full analysis below.

### How to scan

1. **Check dependency manifests first** — most reliable signals:
   * Python: `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`
   * TypeScript/JavaScript: `package.json`

2. **Scan import statements** in source files to confirm what's in use:

   ```bash
   # Python
   grep -rE "^(import|from)\s+(langchain|langgraph|strands|agents|openai|anthropic|boto3|google)" . \
     --include="*.py" -h | sort -u

   # Node.js / TypeScript
   grep -rE "(import|require).*['\"](@langchain|langchain|openai|@anthropic-ai|@aws-sdk|@vercel/ai)" . \
     --include="*.ts" --include="*.js" -h | sort -u
   ```

3. **Check for existing LaunchDarkly setup**:
   * `ldclient`, `@launchdarkly/node-server-sdk` imports
   * `LAUNCHDARKLY_SDK_KEY` in `.env` or config files
   * Existing `LDAIClient` / `LdAiClient` usage

4. **For monorepos or multi-service projects** — ask which service to instrument rather than guessing.

5. **Identify the config mode** — ask the user if they're building:

   * **Completion mode** — a single LLM call per request. The config provides a list of messages (system prompt + optional user/assistant turns) that are sent directly to the model. Good for: chat UIs, summarization, classification, Q\&A.
   * **Agent mode** — multi-step workflows where the model may call tools, loop, or hand off to other agents. The config provides a free-form `instructions` string (the agent's goal or persona) rather than a fixed message list. Good for: ReAct loops, LangGraph graphs, OpenAI Agents SDK, Strands.

   If unsure, read a few source files to infer from usage patterns. If the code calls `.invoke()` / `.chat()` directly, it is likely completion mode. If it uses a `Runner`, a tool-calling loop, or a `Graph`, it is likely agent mode.

### Phase 1 output

Return a concise summary:

* Detected language, AI framework, and model provider
* Config mode (completion or agent)
* Proposed LaunchDarkly AI SDK integration (from routing table below)
* Whether the LaunchDarkly server-side SDK is already installed

**STOP. Present your analysis and wait for user confirmation before proceeding to Phase 2.**

***

## INTEGRATION ROUTING TABLE

### Python

| Detection signal                                              | Framework         | Integration guide                                                                                                      |
| ------------------------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `from langchain` / `langchain-openai` / `langchain-anthropic` | LangChain         | [https://docs.launchdarkly.com/guides/ai-configs/langchain](https://docs.launchdarkly.com/guides/ai-configs/langchain) |
| `from langgraph` / `langgraph` in deps                        | LangGraph         | [https://docs.launchdarkly.com/guides/ai-configs/langgraph](https://docs.launchdarkly.com/guides/ai-configs/langgraph) |
| `from strands import Agent` / `strands-agents`                | Strands Agents    | [https://docs.launchdarkly.com/guides/ai-configs/strands](https://docs.launchdarkly.com/guides/ai-configs/strands)     |
| `from agents import Agent` / `openai-agents`                  | OpenAI Agents SDK | [https://docs.launchdarkly.com/guides/ai-configs/openai](https://docs.launchdarkly.com/guides/ai-configs/openai)       |
| `from claude_agent_sdk` / `claude-agent-sdk`                  | Claude Agent SDK  | [https://docs.launchdarkly.com/guides/ai-configs/anthropic](https://docs.launchdarkly.com/guides/ai-configs/anthropic) |
| `import openai` (direct, no framework)                        | OpenAI SDK        | [https://docs.launchdarkly.com/guides/ai-configs/openai](https://docs.launchdarkly.com/guides/ai-configs/openai)       |
| `import anthropic` (direct, no framework)                     | Anthropic SDK     | [https://docs.launchdarkly.com/guides/ai-configs/anthropic](https://docs.launchdarkly.com/guides/ai-configs/anthropic) |
| `boto3` + Bedrock endpoint                                    | AWS Bedrock       | [https://docs.launchdarkly.com/guides/ai-configs/bedrock](https://docs.launchdarkly.com/guides/ai-configs/bedrock)     |
| `google-generativeai` / `langchain-google-genai`              | Gemini            | [https://docs.launchdarkly.com/guides/ai-configs/gemini](https://docs.launchdarkly.com/guides/ai-configs/gemini)       |

### TypeScript / JavaScript

| Detection signal                                  | Framework               | Integration guide                                                                                                      |
| ------------------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `@langchain/core` / `langchain` in `package.json` | LangChain JS            | [https://docs.launchdarkly.com/guides/ai-configs/langchain](https://docs.launchdarkly.com/guides/ai-configs/langchain) |
| `openai` in `package.json`                        | OpenAI SDK (Node.js)    | [https://docs.launchdarkly.com/guides/ai-configs/openai](https://docs.launchdarkly.com/guides/ai-configs/openai)       |
| `@anthropic-ai/sdk` in `package.json`             | Anthropic SDK (Node.js) | [https://docs.launchdarkly.com/guides/ai-configs/anthropic](https://docs.launchdarkly.com/guides/ai-configs/anthropic) |
| `@ai-sdk/*` / `ai` from Vercel in `package.json`  | Vercel AI SDK           | [https://docs.launchdarkly.com/guides/ai-configs](https://docs.launchdarkly.com/guides/ai-configs)                     |

### Fallback

If no framework matches, start with the quickstart:
[https://docs.launchdarkly.com/home/ai-configs/quickstart](https://docs.launchdarkly.com/home/ai-configs/quickstart)

***

## PHASE 2: IMPLEMENTATION

After the user confirms your Phase 1 analysis, implement the integration.

### 1. Fetch the matched integration guide

Read the guide URL identified in the routing table **before writing any code**. Follow the installation and integration steps from that page exactly.

### 2. Install packages

Install the observability package alongside the AI SDK — it is required to populate the **Observability** and **AgentControl Monitoring** dashboards in LaunchDarkly.

> **Scope of this install — read this before running anything.** The only changes that are in-scope without further consent are adding the **LaunchDarkly packages** named below. Do **not** upgrade, downgrade, pin, or replace any other packages — even if peer-dependency warnings suggest it. Do not run `npm audit fix`, `pnpm update`, `poetry update`, or any bulk-update command. Do not bump the user's framework version (LangChain, OpenAI, etc.) "to match" a newer LaunchDarkly SDK. The user may be on an older version on purpose (downstream compatibility, internal pinning, governance policies you cannot see), and silently changing it is a high-cost mistake.
>
> **If install fails or reports peer conflicts:** stop, surface the exact error, and ask the user how to proceed. Use a structured choice:
>
> > "The install reported `[exact error]`. To resolve it I would need to `[specific change to non-LD packages]`. How would you like to proceed?
> >
> > 1. Yes, make those changes
> > 2. No, keep only the LaunchDarkly packages — I'll resolve the conflict myself
> > 3. Show me the exact commands first"
>
> Do not write the question as plain text — present it as a clear choice and wait for an answer. If the user declines, leave their existing dependencies untouched, install only the LaunchDarkly packages if possible, and proceed.

**Python — pip:**

```bash
# Use a virtual environment to avoid system-package conflicts
python3 -m venv .venv && source .venv/bin/activate
pip install launchdarkly-server-sdk launchdarkly-server-sdk-ai launchdarkly-observability
```

**Python — Poetry:**

```bash
poetry add launchdarkly-server-sdk launchdarkly-server-sdk-ai launchdarkly-observability
```

**Node.js / TypeScript:**

```bash
npm install @launchdarkly/node-server-sdk @launchdarkly/server-sdk-ai @launchdarkly/server-sdk-ai-openai @launchdarkly/observability-node
```

> `@launchdarkly/server-sdk-ai-openai` provides the `getAIMetricsFromResponse` helper used in Step 6. Skip it if you are not using OpenAI directly.

### 2.5. Create the config (automated or manual)

> **Skip this step** if you arrived from the LaunchDarkly in-app onboarding — your config was already created and its key is pre-filled in the `.env` block on the **"Let's hook up your app"** screen. The onboarding auto-creates a writing assistant config (key: `<handle>s-writing-assistant`) with the default model `Anthropic.claude-sonnet-4-6`. If the user's provider key is OpenAI (not Anthropic), fix the model immediately — see the troubleshooting row for "wrong model" below.

If you are **not** coming from in-app onboarding, the config must be created before you can use it.

**Silently probe MCP with `list-ai-configs`. If it succeeds, use Path A — that keeps the user in the agent context. Only fall back to Path B (UI) if MCP is not connected or the call fails.**

In either path, when you reach the SDK-key step, follow the consent flow in [Phase 2 Step 3](#3-set-up-credentials) before fetching or writing the key.

#### Path A — LaunchDarkly MCP (preferred when connected)

1. **Create the config and first variation** using `setup-ai-config`:

   | Field            | Value                                                  |
   | ---------------- | ------------------------------------------------------ |
   | `projectKey`     | User's LaunchDarkly project key                        |
   | `key`            | Stable identifier, e.g. `"my-chatbot"`                 |
   | `name`           | Human-readable, e.g. `"My Chatbot"`                    |
   | `mode`           | `"completion"` or `"agent"` (from Phase 1)             |
   | `variationKey`   | `"v1"` or `"production-initial"`                       |
   | `variationName`  | `"Production (initial)"`                               |
   | `modelConfigKey` | `"Provider.model-id"` — see table in reference section |
   | `modelName`      | Model identifier string (e.g. `"gpt-5.4"`)             |
   | `messages`       | *(completion mode)* system/user messages array         |
   | `instructions`   | *(agent mode)* goal/persona string                     |
   | `parameters`     | `{"temperature": 0.7, "max_tokens": 2000}` etc.        |

2. **Set the default targeting rule** using `update-rollout` (Feature Management MCP):
   * `flagKey` = the config key (configs are flags under the hood)
   * `env` = environment key (e.g. `"production"`, `"test"`, `"development"`)
   * `rolloutType` = `"variation"`, `variationIndex` = `0`

3. **Get the SDK key** using `get-project`:
   * Use the `sdkKey` from the matching environment — put it in `.env` as `LAUNCHDARKLY_SDK_KEY`

#### Path B — LaunchDarkly UI (always available)

1. Left sidebar → **Create** → **AgentControl** → select mode → set name and key → **Create**
2. **Variations** tab → fill in model, parameters, and prompt or instructions
3. **Targeting** tab → Default rule → serve your new variation → **Review and save**
4. **Account settings** → **Environments** → copy the SDK key for your environment

***

### 3. Set up credentials

> **Tip:** If you arrived here from the LaunchDarkly in-app onboarding, the values below are already filled in on the **"Let's hook up your app"** screen. Copy them from the `.env` block shown there and paste them into your `.env` file.

#### Ask before writing any secret — BLOCKING

Before fetching, writing, or pasting an SDK key, config key, or provider API key into any file in the user's repo, **stop and ask the user how they want secrets handled**. Some users keep `.env` under tight controls (CI-only, encrypted vaults, secret managers) and silently writing to it is unsafe. Use a structured choice — present these three options exactly:

> "Before I add the LaunchDarkly SDK key (and any provider keys), how would you like to set up secrets?
>
> 1. **Tell me where to put it** — give me a file path or secrets-manager command and I'll write it only there.
> 2. **I'll set it up myself** — just tell me the variable names I need and I'll handle the values.
> 3. **Write to `.env` for me** — I'll create or update `.env` and ensure it's in `.gitignore`."

**Behavior per option:**

* **Option 1 (Tell me where):** ask for the exact path or command. Ask whether the user will paste the key or wants the agent to fetch it via MCP (`get-project` — see [Fetching the SDK key via MCP](#fetching-the-sdk-key-via-mcp) below). Write the key only to the location they named. Do not create `.env` or modify any other file.
* **Option 2 (I'll do it myself):** list the variable names and the matching LaunchDarkly UI page (Account settings → Environments). Wait for the user to confirm the variables are set before continuing. Do not fetch or write the key value at all.
* **Option 3 (Write to `.env`):** ensure `.env` is listed in `.gitignore` at the same root before writing any real value (add the entry if missing). Then create or append-update `.env` with **only** the LaunchDarkly + provider lines below — never remove unrelated variables. If a `.env.example` exists, add placeholder entries (no real keys) so teammates know which variables to set.

If the user has already pasted real values into chat, treat them as sensitive: write only to the location they chose, do not echo full key values back, and do not log them. Keys in agent transcripts may persist beyond the session.

#### Fetching the SDK key via MCP

If the user picks options 1 or 3 and asks the agent to fetch the SDK key, use `get-project` from the Feature Management MCP. The response includes each environment's SDK key, client-side ID, and mobile key — pick the **SDK key** for the environment the user is targeting (typically `production` or `test`). Do not echo the full value in chat. If MCP is not connected, fall back to telling the user to copy it from **Account settings → Environments**.

#### Variable values

`SERVICE_NAME` and `SERVICE_VERSION` are used by the observability plugin to label traces in LaunchDarkly. Use a meaningful service name and your deployed git SHA or release version.

**OpenAI-backed stacks:**

```bash
LAUNCHDARKLY_SDK_KEY=sdk-...          # from LaunchDarkly onboarding UI
LAUNCHDARKLY_AI_CONFIG_KEY=your-ai-config-key  # from LaunchDarkly onboarding UI
OPENAI_API_KEY=sk-...
SERVICE_NAME=my-ai-service
SERVICE_VERSION=1.0.0
```

**Anthropic-backed stacks:**

```bash
LAUNCHDARKLY_SDK_KEY=sdk-...
LAUNCHDARKLY_AI_CONFIG_KEY=your-ai-config-key
ANTHROPIC_API_KEY=sk-ant-...
SERVICE_NAME=my-ai-service
SERVICE_VERSION=1.0.0
```

**Gemini:**

```bash
LAUNCHDARKLY_SDK_KEY=sdk-...
LAUNCHDARKLY_AI_CONFIG_KEY=your-ai-config-key
GOOGLE_API_KEY=...
SERVICE_NAME=my-ai-service
SERVICE_VERSION=1.0.0
```

**AWS Bedrock** — uses boto3 credential chain; no extra key needed, but verify AWS credentials are configured. Add `SERVICE_NAME` and `SERVICE_VERSION` as above.

The LaunchDarkly SDK key is a server-side key that starts with `sdk-`. Find it under **Account settings > Environments** in the LaunchDarkly UI, or fetch it programmatically with the `get-project` MCP tool (see "Fetching the SDK key via MCP" above).

### 4. Add the common setup

Add this once, near application startup, before any agent or model calls. The observability plugin is wired in here — it auto-instruments SDK operations and sends traces to LaunchDarkly so config evaluations appear in both the **Observability** and **AgentControl Monitoring** dashboards.

**Python:**

```python
import os
import ldclient
from ldclient.config import Config
from ldclient.context import Context
from ldai import LDAIClient, AICompletionConfigDefault, AIAgentConfigDefault, ModelConfig, LDMessage
from ldobserve import ObservabilityConfig, ObservabilityPlugin

ldclient.set_config(Config(
    os.environ["LAUNCHDARKLY_SDK_KEY"],
    plugins=[
        ObservabilityPlugin(
            ObservabilityConfig(
                service_name=os.getenv("SERVICE_NAME", "my-ai-service"),
                service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
            )
        )
    ],
))
aiclient = LDAIClient(ldclient.get())

# Replace with the real user or session identifier (e.g. user.id, session_id, request.user).
# This key drives targeting rules, evaluation history, and trace attribution.
current_user_id = os.getenv("USER_ID", "anonymous")
context = Context.builder(current_user_id).kind("user").build()
```

**Node.js / TypeScript:**

```typescript
import { init, type LDContext } from "@launchdarkly/node-server-sdk";
import { Observability } from "@launchdarkly/observability-node";
import {
  initAi,
  type LDAIClient,
  type LDAIAgentConfig,
  type LDAICompletionConfig,
} from "@launchdarkly/server-sdk-ai";

const ldClient = init(process.env.LAUNCHDARKLY_SDK_KEY!, {
  plugins: [
    new Observability({
      serviceName: process.env.SERVICE_NAME ?? "my-ai-service",
      serviceVersion: process.env.SERVICE_VERSION ?? "1.0.0",
    }),
  ],
});

await ldClient.waitForInitialization({ timeout: 10 });
const aiClient: LDAIClient = initAi(ldClient);

// Replace with the real user or session identifier (e.g. req.user.id, session.id).
// This key drives targeting rules, evaluation history, and trace attribution.
const currentUserId = process.env.USER_ID ?? "anonymous";
const context: LDContext = { kind: "user", key: currentUserId };
```

### 5. Evaluate the config

Each call returns a single config object. Get a tracker by calling `tracker = config.create_tracker()` (Python) or `const tracker = config.createTracker()` (Node.js) — call this once per request, after the `enabled` check, and use that same tracker for all metric calls in the request.

> **Always provide a `default=` value.** Without one, the SDK returns `enabled=False` whenever LaunchDarkly is unreachable — including during first-time setup before the SDK connects. The default must duplicate the exact hardcoded values from the original code so behavior is identical during outages. `ModelConfig`, `LDMessage`, `AICompletionConfigDefault`, and `AIAgentConfigDefault` are imported in Step 4.

**Agent mode (Python):**

```python
config = aiclient.agent_config(
    os.environ["LAUNCHDARKLY_AI_CONFIG_KEY"],
    context,
    default=AIAgentConfigDefault(
        enabled=True,
        model=ModelConfig(name="gpt-5.4"),          # ← your hardcoded model
        instructions="You are a helpful assistant.", # ← your hardcoded prompt
    ),
)
if not config.enabled:
    # config is explicitly disabled in the LaunchDarkly UI.
    return "I'm sorry, this feature is temporarily unavailable."
tracker = config.create_tracker()   # call once per request, after enabled check
# config.instructions    → system prompt / agent goal (str)
# config.model.name      → model identifier (str)
# tracker                → LDAIConfigTracker for metrics (see step 7)
```

**Agent mode (Node.js):**

```typescript
const agentConfig = await aiClient.agentConfig(
  process.env.LAUNCHDARKLY_AI_CONFIG_KEY!,
  context,
  {                                    // default — mirrors your hardcoded values
    enabled: true,
    model: { name: "gpt-5.4" },
    instructions: "You are a helpful assistant.",
  },
);
if (!agentConfig.enabled) {
  // config is explicitly disabled in the LaunchDarkly UI.
  return "I'm sorry, this feature is temporarily unavailable.";
}
const tracker = agentConfig.createTracker();
```

**Completion mode (Python):**

```python
config = aiclient.completion_config(
    os.environ["LAUNCHDARKLY_AI_CONFIG_KEY"],
    context,
    default=AICompletionConfigDefault(
        enabled=True,
        model=ModelConfig(name="gpt-5.4"),          # ← your hardcoded model
        messages=[
            LDMessage(role="system", content="You are a helpful assistant."),  # ← your hardcoded prompt
        ],
    ),
    variables={"example_variable": "value"},        # optional — omit if not using template variables
)
if not config.enabled:
    # config is explicitly disabled in the LaunchDarkly UI.
    return "I'm sorry, this feature is temporarily unavailable."
tracker = config.create_tracker()   # call once per request, after enabled check
# config.messages            → list[LDMessage] to pass to the model
# config.model.name          → model identifier
# tracker                    → LDAIConfigTracker for metrics
```

**Completion mode (Node.js):**

```typescript
const aiConfig = await aiClient.completionConfig(
  process.env.LAUNCHDARKLY_AI_CONFIG_KEY!,
  context,
  {                                    // default — mirrors your hardcoded values
    enabled: true,
    model: { name: "gpt-5.4" },
    messages: [{ role: "system", content: "You are a helpful assistant." }],
  },
  { example_variable: "value" },       // optional template variables — omit if unused
);
if (!aiConfig.enabled) {
  // config is explicitly disabled in the LaunchDarkly UI.
  return "I'm sorry, this feature is temporarily unavailable.";
}
const tracker = aiConfig.createTracker();
```

### 6. Add the framework-specific handler

Read the integration guide fetched in step 1 for the exact handler. The snippets below are starting points only — prefer the guide's code.

**Observability is automatic** — the `ObservabilityPlugin` wired in during Step 4 auto-instruments OpenAI, LangChain, and other supported frameworks via OpenTelemetry. You do not need to add decorators or manual span code to get traces. For custom providers or unsupported frameworks, see NEXT STEP 4 for manual span creation.

> **Model name pattern:** `config.model` can be `None` if the config variation has no model configured. Always provide a hard-coded fallback: `model_name = config.model.name if config.model else "gpt-5.4"`. Choose the fallback that matches your stack (e.g. `"claude-sonnet-4-6"` for Anthropic, `"o4-mini"` for a cost-optimized OpenAI option).

**OpenAI SDK — direct calls (Python):**

```python
from openai import OpenAI
from ldai_openai import get_ai_metrics_from_response

openai_client = OpenAI()

def handle_call(config, user_input: str):
    tracker = config.create_tracker()
    model_name = config.model.name if config.model else "gpt-5.4"
    # OpenAI spans are emitted automatically by the observability plugin — no decorator needed.
    return tracker.track_metrics_of(
        get_ai_metrics_from_response,
        lambda: openai_client.chat.completions.create(
            model=model_name,
            messages=[m.to_dict() for m in (config.messages or [])] + [{"role": "user", "content": user_input}],
        ),
    )
```

**OpenAI SDK — direct calls (Node.js):**

```typescript
import { OpenAI } from "openai";
import { getAIMetricsFromResponse } from "@launchdarkly/server-sdk-ai-openai";

const openaiClient = new OpenAI();

async function handleCall(aiConfig: LDAICompletionConfig, userInput: string) {
  const tracker = aiConfig.createTracker();
  return tracker.trackMetricsOf(
    getAIMetricsFromResponse,
    async () => openaiClient.chat.completions.create({
      model: aiConfig.model?.name ?? "gpt-5.4",
      messages: [...(aiConfig.messages ?? []), { role: "user", content: userInput }],
    }),
  );
}
```

**LangChain — agent mode (Python):** *(uses `config.instructions` — free-form agent goal)*

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.callbacks import get_openai_callback
from ldai.tracker import TokenUsage

def handle_call(config, user_input: str) -> str:
    tracker = config.create_tracker()
    model_name = config.model.name if config.model else "gpt-5.4"
    llm = ChatOpenAI(model=model_name)
    messages = []
    if config.instructions:
        messages.append(SystemMessage(content=config.instructions))
    messages.append(HumanMessage(content=user_input))
    with get_openai_callback() as cb:
        response = llm.invoke(messages)
    tracker.track_tokens(TokenUsage(
        input=cb.prompt_tokens,
        output=cb.completion_tokens,
        total=cb.total_tokens,
    ))
    tracker.track_success()
    return response.content
```

**LangChain — completion mode (Python):** *(uses `config.messages` — structured message list)*

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.callbacks import get_openai_callback
from ldai.tracker import TokenUsage

def handle_call(config, user_input: str) -> str:
    tracker = config.create_tracker()
    model_name = config.model.name if config.model else "gpt-5.4"
    llm = ChatOpenAI(model=model_name)
    # config.messages is a list[LDMessage] from the config variation
    lc_messages = []
    for m in (config.messages or []):
        if m.role == "system":
            lc_messages.append(SystemMessage(content=m.content))
        elif m.role == "assistant":
            lc_messages.append(AIMessage(content=m.content))
        else:
            lc_messages.append(HumanMessage(content=m.content))
    lc_messages.append(HumanMessage(content=user_input))
    with get_openai_callback() as cb:
        response = llm.invoke(lc_messages)
    tracker.track_tokens(TokenUsage(
        input=cb.prompt_tokens,
        output=cb.completion_tokens,
        total=cb.total_tokens,
    ))
    tracker.track_success()
    return response.content
```

**OpenAI Agents SDK (Python):**

```python
from agents import Agent
from agents.run import Runner

async def handle_call(config, user_input: str) -> str:
    tracker = config.create_tracker()
    model_name = config.model.name if config.model else "gpt-5.4"
    agent = Agent(name="assistant", instructions=config.instructions or "", model=model_name)
    result = await Runner.run(agent, user_input)
    tracker.track_success()
    return result.final_output
```

**Strands (Python):**

```python
from strands import Agent
from strands.models.openai import OpenAIModel

async def handle_call(config, user_input: str) -> str:
    tracker = config.create_tracker()
    model_name = config.model.name if config.model else "gpt-5.4"
    openai_model = OpenAIModel(model_id=model_name)
    agent = Agent(system_prompt=config.instructions or "", model=openai_model, callback_handler=None)
    result = str(agent(user_input))
    tracker.track_success()
    return result
```

**Claude Agent SDK (Python):**

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import ResultMessage

async def handle_call(config, user_input: str) -> str:
    tracker = config.create_tracker()
    model_name = config.model.name if config.model else "claude-sonnet-4-6"
    final_message = None
    async for message in query(
        prompt=user_input,
        options=ClaudeAgentOptions(system_prompt=config.instructions or "", model=model_name),
    ):
        final_message = message
    if not isinstance(final_message, ResultMessage):
        raise ValueError(f"Unexpected message type: {type(final_message)}")
    tracker.track_success()
    return final_message.result or ""
```

For Node.js non-OpenAI frameworks, refer to: [https://docs.launchdarkly.com/sdk/observability/nodejs](https://docs.launchdarkly.com/sdk/observability/nodejs)

### 7. Track metrics and token usage

`tracker = config.create_tracker()` (Python) / `const tracker = config.createTracker()` (Node.js) must record every call outcome. This is what populates the **AgentControl Monitoring** dashboard. Create the tracker once per request, after the `enabled` check.

**Python — modern API for OpenAI (preferred):**

```python
from ldai_openai import get_ai_metrics_from_response

tracker = config.create_tracker()
response = tracker.track_metrics_of(
    get_ai_metrics_from_response,
    lambda: openai_client.chat.completions.create(model=..., messages=...),
)
```

> **Note:** `tracker.track_metrics_of(extractor, fn)` runs the call, applies the extractor to its response, and records duration, tokens, and success/error in one shot. Every provider goes through `track_metrics_of` with the appropriate extractor — `get_ai_metrics_from_response` from `ldai_openai` for OpenAI, or a small custom extractor for Anthropic, Bedrock, Gemini, and others. See [NEXT STEP 11](#next-step-11-complete-the-migration-existing-app-users) for extractor examples covering Anthropic, Bedrock, and Gemini.

**Python — manual tracking for other frameworks:**

```python
from ldai.tracker import TokenUsage

tracker = config.create_tracker()
try:
    result = handle_call(config, user_input)        # handler must call tracker.track_success() internally
    # Optionally add token tracking if the framework exposes usage:
    # tracker.track_tokens(TokenUsage(
    #     input=usage.prompt_tokens,
    #     output=usage.completion_tokens,
    #     total=usage.total_tokens,
    # ))
except Exception:
    tracker.track_error()
    raise
```

> Note: `track_tokens` takes a `TokenUsage` dataclass (`from ldai.tracker import TokenUsage`), not a plain dict.

**Node.js — recommended shortcut for OpenAI (auto-tracks everything):**

```typescript
import { getAIMetricsFromResponse } from "@launchdarkly/server-sdk-ai-openai";

const tracker = aiConfig.createTracker();
const response = await tracker.trackMetricsOf(
  getAIMetricsFromResponse,
  async () => openaiClient.chat.completions.create({ model: ..., messages: ... }),
);
```

**Node.js — manual tracking for other frameworks:**

```typescript
const tracker = aiConfig.createTracker();
try {
  const result = await runAgent(agentConfig, userInput);
  tracker.trackTokens({ input: 0, output: 0, total: 0 });  // fill in from your framework
  tracker.trackSuccess();
} catch (e) {
  tracker.trackError();
  throw e;
}
```

> **LangChain always exposes token counts** via `get_openai_callback()` — always wrap LangChain calls in that context manager and call `tracker.track_tokens()` (see the LangChain snippets above). `tracker.track_success()` alone does not send token data; cost and token metrics in the Monitoring dashboard derive entirely from `track_tokens()`. For frameworks that genuinely do not expose token counts, omit `track_tokens` / `trackTokens` — success/error tracking alone is sufficient to populate request count and error rate.

### 8. Implementation rules

* Read credentials from environment variables — never hardcode SDK keys or API keys
* Initialize the LaunchDarkly client **once** at startup, before any agent or model calls
* Always include the observability plugin in the `Config`/`init` call — required for traces to appear
* Call `agent_config()` / `completion_config()` (Python) or `agentConfig()` / `completionConfig()` (Node.js) **once per request** — never cache the returned config across requests
* Python: call `tracker = config.create_tracker()` once per request (after the `enabled` check) to get the tracker
* Node.js: call `const tracker = config.createTracker()` once per request to get a fresh tracker
* Traces are emitted automatically by the observability plugin — no `@observe` decorator or manual span code is needed for standard frameworks (OpenAI, LangChain)
* Always provide a `default=` argument to `completion_config()` / `agent_config()` — without one, the SDK returns `enabled=False` when LaunchDarkly is unreachable (including during first-time setup)
* Always provide a fallback model name in case `config.model` is `None`
* Always call `tracker.track_success()` or `tracker.track_error()` after every AI call (or use `tracker.track_metrics_of(extractor, fn)` / `tracker.trackMetricsOf(extractor, fn)` which handle this automatically)

***

## VERIFICATION

After implementation:

1. **Run the application** and trigger at least one AI call through the integrated path
2. **Check the LaunchDarkly UI** — the in-app onboarding will show **Connected** once the SDK evaluates the config
3. **Check the Observability tab** — traces from the observability plugin should appear within 1–2 minutes of the first call
4. **Check the AgentControl Monitoring tab** — token usage, latency, and success/error rates appear within 1–2 minutes of the first tracked call

> **Set the user's expectations on data delay.** Tell the user up front: *"After your first AI call, the **Connected** state usually flips within seconds, but **monitoring data, traces, and judge scores typically take 1–2 minutes** to appear in their respective tabs — and sometimes a bit longer. If a tab looks empty right after a call, refresh after a minute or two before troubleshooting."* Saying this once at verification time prevents the very common "I made a call but the dashboard is empty, what's wrong?" cycle.

**Troubleshooting checklist:**

| Symptom                                                                                                                        | Check                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "Connected" never appears                                                                                                      | Confirm `track_success()` or `track_error()` is called after each AI call                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Observability tab is empty                                                                                                     | Confirm `ObservabilityPlugin` / `Observability` is included in the SDK `plugins` array at init                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Traces not linked to config                                                                                                    | Confirm the `ObservabilityPlugin` is in the `plugins` array; for custom providers, wrap calls in `with observe.start_span("name"):`                                                                                                                                                                                                                                                                                                                                                                                                   |
| AgentControl Monitoring shows no data                                                                                          | Confirm `track_success()` / `track_error()` is called; `track_tokens` is required for token and cost metrics                                                                                                                                                                                                                                                                                                                                                                                                                          |
| LangChain: token usage and cost never appear in Monitoring                                                                     | `tracker.track_success()` alone does not send token counts — wrap LangChain calls in `get_openai_callback() as cb` and call `tracker.track_tokens(TokenUsage(input=cb.prompt_tokens, output=cb.completion_tokens, total=cb.total_tokens))` before `tracker.track_success()`. LangChain's map-reduce and chain patterns make multiple internal LLM calls; the callback aggregates them all.                                                                                                                                            |
| Python `AttributeError: cannot unpack`                                                                                         | `agent_config()` and `completion_config()` return a single object — use `config = aiclient.agent_config(...)`, then `tracker = config.create_tracker()`                                                                                                                                                                                                                                                                                                                                                                               |
| Python `AttributeError: model_config`                                                                                          | The completion method is `completion_config()`, not `model_config()`                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Python `TypeError: track_tokens`                                                                                               | `track_tokens` takes a `TokenUsage` dataclass, not a dict: `from ldai.tracker import TokenUsage`                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Node.js `TypeError: agentConfig is not a function`                                                                             | Check `initAi(ldClient)` was called and returned the AI client before use                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Node.js `tracker is undefined`                                                                                                 | Call `config.createTracker()` to get a tracker; do not destructure `{ tracker }` from the config result                                                                                                                                                                                                                                                                                                                                                                                                                               |
| SDK key error at startup                                                                                                       | Verify `LAUNCHDARKLY_SDK_KEY` starts with `sdk-` and is a server-side key                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Config key not found                                                                                                           | Confirm the key in code matches the config key shown in the LaunchDarkly UI                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `config.enabled` is `false` on every call                                                                                      | Either the config has targeting off, or no `default=` was provided — add `default=AICompletionConfigDefault(enabled=True, ...)` with your hardcoded values so the app works when LaunchDarkly is unreachable                                                                                                                                                                                                                                                                                                                          |
| `NameError: name 'current_user_id' is not defined` (Python)                                                                    | Add `current_user_id = os.getenv("USER_ID", "anonymous")` before the `Context.builder(...)` line                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `ReferenceError: currentUserId is not defined` (Node.js)                                                                       | Add `const currentUserId = process.env.USER_ID ?? "anonymous";` before the `context` object literal                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Lots of `ERROR` / `WARNING` logs at startup with a fake SDK key                                                                | Expected — the SDK tries to connect and logs failures. Use a real SDK key from LaunchDarkly and the logs disappear                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Node.js: initialization timeout                                                                                                | Increase timeout in `waitForInitialization({ timeout: 10 })` or check network access                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Config has the wrong model for the user's provider (e.g. Anthropic `claude-sonnet-4-6` preset, but the user has an OpenAI key) | The in-app onboarding pre-creates a variation with `Anthropic.claude-sonnet-4-6` as the default — if the user only has an OpenAI API key, the model call will fail. **Fix it from the agent — do not send the user to the UI.** If MCP is connected, call `update-ai-config-variation` with the matching `modelConfigKey` (e.g. `"OpenAI.gpt-5.4"`) and `modelName` (e.g. `"gpt-5.4"`) and tell the user you've corrected it. Only fall back to "open the variation in the LaunchDarkly UI and edit the model" if MCP is unavailable. |
| User reports the AI call errors at runtime even though the dashboard shows **Connected**                                       | "Connected" only confirms the SDK reported back to LaunchDarkly. The model call itself can still fail (wrong model name for the provider, missing or expired provider API key, framework version mismatch). Read the actual exception in the user's terminal output before guessing — do not assume the integration is healthy because the badge turned green.                                                                                                                                                                        |

***

## WHAT'S NEXT

Once the user confirms "Connected" appears in the LaunchDarkly UI:

**Step 1 — Acknowledge and direct them to the Monitoring tab:**

> "Your SDK is connected — nice work. Before we go further, head over to your config → **Monitoring** tab. After a minute or two of AI calls flowing through, you'll start seeing token usage, latency, and request counts broken down by variation. Make a few AI calls if you haven't already, give it a moment, and refresh the page. This is where you'll track the real cost and performance impact of every prompt and model change you make."

**Step 2 — Present the next-steps menu:**

**If the user came from Phase 1 (existing app integration)**, lead with option 11 — completing the full migration is the highest-value next step for them. **If they used the sample app path**, option 11 is not yet relevant; start from option 1.

Say:

> "You just experienced the core value of AgentControl: you changed a prompt or model in the LaunchDarkly UI and your running app picked it up immediately — no redeploy needed. That's the foundation. Here's what to explore next:"

Then present the following menu with each section clearly separated — never run items together into a single paragraph:

***

**If you have more hardcoded prompts or models to extract:**

11. **Complete the migration** — extract every remaining hardcoded prompt, model, parameter, and tool into configs in five structured stages

***

**Core next steps**

1. **Invite your team** — give teammates access to edit prompts and models in the LaunchDarkly UI, no code needed
2. **Add a judge** — automatically score every AI response for accuracy, relevance, and toxicity
3. **Run your first eval** — test prompt variations against each other before going to production
4. **View your monitoring data** — token costs, latency, and error rates on the Monitoring tab
5. **Log traces** — see full request traces linked to config evaluations in the Observability tab
6. **Explore more SDK features** — streaming, `create_model`, multi-agent configs

***

**Advanced topics**

7. **Agent graphs** — orchestrate multi-agent workflows, defined via the AgentControl MCP or the LaunchDarkly UI
8. **Run an experiment** — A/B test prompt or model variations against real user behavior metrics
9. **Guarded rollouts** — automatically pause or roll back a model change if quality scores drop
10. **Governance and approvals** — require review before any config change reaches production

***

Ask: "Which would you like to explore?"

**Wait for the user to choose. Then follow the guidance for that topic below. Read the referenced docs URL before writing any code or describing UI steps.**

**After completing any topic, re-offer the menu. Acknowledge what they just accomplished, note which steps they've done, and suggest the most logical next step — guide them progressively toward the full product rather than just dumping the entire list again.**

***

### NEXT STEP 1: Invite your team

**What this unlocks:** Once your config is running, anyone on your team — product managers, ML engineers, or other developers — can edit prompts, swap models, and update parameters directly in the LaunchDarkly UI. No code changes or redeployment required. This is one of the core value propositions of AgentControl: separating model configuration from application code so the people closest to the product can iterate on their own.

Docs: [https://docs.launchdarkly.com/home/account/members](https://docs.launchdarkly.com/home/account/members)

**Prefer MCP when connected.** The Feature Management MCP exposes `invite-members` — invite teammates from the agent in one call instead of asking the user to switch to the UI. Confirm the role with the user first if it's not obvious from context.

```
invite-members:
  emails: ["alice@example.com", "bob@example.com"]
  role: "writer"      # or "reader" / "admin"
```

**UI fallback** (use only if MCP is not connected):

1. Go to **Account settings** → **Members**.
2. Click **Invite members**.
3. Enter one or more email addresses.
4. Assign a role:
   * **Writer** — can create and edit configs, variations, targeting rules, and tools. Recommended for anyone who will manage prompts or models.
   * **Reader** — view-only access. Good for stakeholders who want to review monitoring data without making changes.
   * **Admin** — full account access, including environment and project settings.
5. Click **Send invite**. Recipients get an email link to join the LaunchDarkly account.

**What to tell teammates once they're in:**

* Open the config → **Variations** tab → edit the system prompt or swap the model → **Review and save**. The change goes live immediately — no deployment needed.
* Use the **LLM Playground** (top right of the Variations tab) to compare prompt or model options side-by-side before committing.
* Check the **Monitoring** tab for real-time token costs, latency, and error rates broken down by variation.

**Custom roles (Enterprise):** custom roles let you grant fine-grained permissions — for example, write access to configs only, scoped to specific projects or environments, without touching feature flags. Contact your LaunchDarkly admin to configure this. See: [https://docs.launchdarkly.com/home/account/role-create](https://docs.launchdarkly.com/home/account/role-create)

***

### NEXT STEP 2: Add a judge

**What this unlocks:** Every AI response is automatically scored (0.0–1.0) for Accuracy, Relevance, and Toxicity. Scores appear on the Monitoring tab and can trigger guarded rollout pauses.

Docs: [https://docs.launchdarkly.com/home/ai-configs/online-evaluations](https://docs.launchdarkly.com/home/ai-configs/online-evaluations)

**Tailor by mode detected in Phase 1:**

#### If completion mode — attach a judge to a variation

**Prefer MCP when connected.** Pass `judgeConfiguration` to `update-ai-config-variation` (or `create-ai-config-variation` for a new variation) to attach judges programmatically — keep the user in the agent context. Confirm the sampling rate with the user first; 10–20% is a reasonable starting default to control cost.

```
update-ai-config-variation:
  projectKey: "my-project"
  configKey: "chat-assistant"
  variationKey: "production-initial"
  judgeConfiguration:
    judges:
      - key: "accuracy"
        sampling: 0.20
      - key: "relevance"
        sampling: 0.20
      - key: "toxicity"
        sampling: 0.20
```

**UI fallback** (use only if MCP is not connected or `judgeConfiguration` isn't in the live tool schema):

1. Open your config → **Variations** tab → click into a variation.
2. In the **Judges** section, click **+ Attach judges**.
3. Select **Accuracy**, **Relevance**, and/or **Toxicity**. Start at 10–20% sampling to control cost.
4. Click **Review and save**.

Then update the call site to await evaluation results:

**Python — `create_model` pattern (recommended for completion mode):**

```python
import asyncio
model = await aiclient.create_model(
    os.environ["LAUNCHDARKLY_AI_CONFIG_KEY"],
    context,
)
if not model:
    print("config disabled or unreachable — using fallback")
    # return fallback here
else:
    response = await model.run(user_input)
    print("Response:", response.content)

    # Await judge evaluations before the request ends
    if response.evaluations:
        results = await asyncio.gather(*response.evaluations)
        for r in results:
            print("Judge result:", r.to_dict())
```

**Node.js sample:** `js-core/packages/sdk/server-ai/examples/chat-judge`

#### If agent mode — invoke a judge directly in code

Agent-mode variations cannot have judges attached in the UI. Use programmatic evaluation:

1. **Create a judge config in LaunchDarkly.** If MCP is connected, use `setup-ai-config` with a judge mode and a built-in or custom judge — do this from the agent rather than sending the user to the UI. If MCP is not available, walk the user through **AgentControl → Create → choose a built-in judge or custom** in the UI.
2. Add its key to your environment: `LAUNCHDARKLY_AI_JUDGE_KEY=your-judge-key` (use the SDK key consent flow from [Phase 2 Step 3](#3-set-up-credentials) before writing it).

**Python:**

```python
from ldai import AICompletionConfigDefault

judge = await aiclient.create_judge(
    os.environ["LAUNCHDARKLY_AI_JUDGE_KEY"],
    context,
    AICompletionConfigDefault(enabled=False),
)

if judge and judge.enabled:
    result = await judge.evaluate(user_input, agent_response)
    print("Judge score:", result.to_dict())
    # Optionally link the score to your agent's config tracker:
    # tracker.track_judge_result(result)  # tracker = config.create_tracker()
```

#### Check the Monitoring tab for judge results

Once the judge is wired up and a few requests have been scored, direct the user here. **Set the delay expectation explicitly** — this is the most common point of confusion in onboarding:

> "Now head over to your config → **Monitoring** tab. Scroll down to the **User satisfaction** section — that's where judge scores (accuracy, relevance, toxicity) appear as they accumulate. **Heads up: judge scores are not instant.** Expect a **1–2 minute delay** (sometimes a bit more for the very first scores) between making the AI call and seeing the score on this tab. If you don't see anything yet, that's almost always the answer — wait a minute or two, refresh the page, and the scores will appear. Once you have data, you can see how scores differ across variations — that's what makes guarded rollouts and experiments meaningful."

***

### NEXT STEP 3: Run your first eval

**What this unlocks:** Compare prompt or model variations against known inputs before they go live. The LLM Playground lets you test side-by-side in the browser; offline evals let you run repeatable tests against a dataset.

Docs: [https://docs.launchdarkly.com/home/ai-configs/offline-evaluations](https://docs.launchdarkly.com/home/ai-configs/offline-evaluations)\
Playground: [https://docs.launchdarkly.com/home/ai-configs/playground](https://docs.launchdarkly.com/home/ai-configs/playground)\
Datasets: [https://docs.launchdarkly.com/home/ai-configs/datasets](https://docs.launchdarkly.com/home/ai-configs/datasets)

**Prefer MCP for setup.** Datasets, evaluations, and playgrounds all have MCP tool coverage. The agent can create the dataset, set up the evaluation, run it, and report the summary back without ever leaving the chat:

```
# 1. Create a dataset of inputs (and optional expected outputs)
create-dataset:
  projectKey: "my-project"
  key: "qa-baseline"
  rows:
    - input: "What is feature flagging?"
      expected: "..."
    - input: "How does a canary deployment work?"
      expected: "..."

# 2. Create an evaluation that ties the dataset to one or more config variations
create-evaluation:
  projectKey: "my-project"
  key: "v1-vs-v2"
  datasetKey: "qa-baseline"
  configKey: "chat-assistant"
  variationKeys: ["production-initial", "shorter-prompt"]
  judges: ["accuracy", "relevance"]

# 3. Run it and fetch the summary when it's done
run-evaluation:
  projectKey: "my-project"
  evaluationKey: "v1-vs-v2"

get-evaluation-run-summary:
  projectKey: "my-project"
  evaluationKey: "v1-vs-v2"
  runId: "...returned by run-evaluation..."
```

For interactive side-by-side comparison (the LLM Playground UI experience), still use the browser — but the underlying playground objects can be created and updated via `create-playground` / `update-playground` so the agent can pre-populate them.

**UI fallback** (use only if the corresponding MCP tools aren't listed):

1. Open your config → click **LLM Playground** (top right of the Variations tab).
2. Add a second variation (different model or prompt wording).
3. Enter a test input and compare responses side-by-side.
4. For repeatable batch testing: go to **Configs → Datasets → New dataset**, upload input/output pairs, then run an offline evaluation from the Playground.

**For programmatic evaluation in CI** (when you want the eval to run as part of your build):

```python
judge = await aiclient.create_judge(
    os.environ["LAUNCHDARKLY_AI_JUDGE_KEY"],
    context,
    AICompletionConfigDefault(enabled=False),
)

test_cases = [
    ("What is feature flagging?", expected_answer_1),
    ("How does a canary deployment work?", expected_answer_2),
]

for input_text, expected in test_cases:
    actual = your_model_call(input_text)
    if judge and judge.enabled:
        result = await judge.evaluate(input_text, actual)
        print(f"Score: {result.to_dict()}")
```

Python sample: `poetry run direct-judge-example` in `hello-python-ai`

***

### NEXT STEP 4: View your monitoring data

**What this unlocks:** The Monitoring tab shows tokens consumed, cost, latency (P50/P95/P99), error rate, and user satisfaction — per variation — so you can compare the real cost and performance of different prompts and models.

Docs: [https://docs.launchdarkly.com/home/ai-configs/monitor](https://docs.launchdarkly.com/home/ai-configs/monitor)

**In the LaunchDarkly UI:**

1. Open your config → click the **Monitoring** tab.
2. If charts appear: you're already sending data. Explore the variation-level breakdown.
3. If charts are empty or show "Waiting for data": **this is expected immediately after your first call.** Monitoring data, traces, and judge scores typically take **1–2 minutes** to appear (sometimes a bit longer for the very first batch). Wait a couple of minutes, then refresh — you should see the data populate. **Tell the user this delay is normal before they start troubleshooting.**
4. If nothing appears after a few minutes: confirm `track_success()` / `track_error()` is called after each AI call (see Phase 2, Step 7).

If `track_metrics_of` (Python) or `trackMetricsOf` (Node.js) is used (from Step 6/7 of Phase 2), token data flows automatically. To add **user satisfaction** signals:

**Python — same-request feedback (thumbs up/down in the response):**

```python
from ldai.tracker import FeedbackKind

# tracker was obtained via tracker = config.create_tracker() earlier in the request
tracker.track_feedback({"kind": FeedbackKind.Positive})   # thumbs up
tracker.track_feedback({"kind": FeedbackKind.Negative})   # thumbs down
```

**Python — async feedback (feedback arrives in a later request):**

At generation time, save the resumption token alongside the response:

```python
# At generation time — serialize and return alongside the response
token = tracker.resumption_token
response_payload = {"text": response_text, "ld_token": token}
```

When feedback arrives later (separate request, separate process):

```python
result = aiclient.create_tracker(token, context)
if result.is_success():
    late_tracker = result.value
    late_tracker.track_feedback({"kind": FeedbackKind.Positive})
```

**Node.js:**

```typescript
tracker.trackFeedback({ kind: LDFeedbackKind.Positive });
// For async feedback: use tracker.resumptionToken and aiClient.createTracker(token, context)
```

***

### NEXT STEP 5: Log traces

**What this unlocks:** Full distributed traces visible in the Observability tab, showing every span in the request with timing, model inputs/outputs, and tool calls — automatically linked to which config variation was served.

Docs: [https://docs.launchdarkly.com/home/ai-configs/manual-llm-span-tracing](https://docs.launchdarkly.com/home/ai-configs/manual-llm-span-tracing)\
Python reference: [https://docs.launchdarkly.com/sdk/observability/python](https://docs.launchdarkly.com/sdk/observability/python)

If the observability plugin is already wired into the SDK init (Phase 2, Step 4), traces are emitting **automatically** for standard frameworks (OpenAI, LangChain, etc.). To verify:

1. Run the app and trigger an AI call.
2. In LaunchDarkly, go to **Observability** in the left sidebar → **Traces** tab.
3. Traces appear within 1–2 minutes. If nothing appears after several calls, confirm the `ObservabilityPlugin` is in the `plugins` array at init.

**If you need to create a manual span** (custom provider, unsupported framework, or to group multiple calls under one named trace):

```python
from ldobserve import observe  # observe is a module singleton, not a decorator

with observe.start_span("my-agent-call") as span:
    # all AI SDK calls inside this block are linked to this span
    tracker = config.create_tracker()
    result = my_model_call(config, user_input)
    tracker.track_success()
```

**If you need to annotate a span with custom LLM attributes** (for custom providers):

```python
from ldobserve import observe
from opentelemetry import trace

with observe.start_span("custom-llm-call") as span:
    span.set_attribute("gen_ai.request.model", "my-model")
    span.set_attribute("gen_ai.system", "my-provider")
    result = my_custom_llm(prompt)
    span.set_attribute("gen_ai.response.finish_reasons", ["stop"])
```

***

### NEXT STEP 6: Explore more SDK features

**What this unlocks:** Higher-level SDK abstractions (`create_model`, multi-agent configs, streaming) that reduce boilerplate, auto-handle tracking, and give you multi-session and multi-agent patterns out of the box.

Python SDK: [https://docs.launchdarkly.com/sdk/ai/python](https://docs.launchdarkly.com/sdk/ai/python)\
Node.js SDK: [https://docs.launchdarkly.com/sdk/ai/nodejs](https://docs.launchdarkly.com/sdk/ai/nodejs)

**Tailor by what the user currently has:**

If they are using low-level `completion_config` + manual model calls → show `create_model`:

**Python — `create_model` (auto-tracks tokens, duration, success):**

```python
model = await aiclient.create_model(
    os.environ["LAUNCHDARKLY_AI_CONFIG_KEY"],
    context,
    variables={"username": "Sandy"},
)
if not model:
    # disabled or LD unreachable — return a hard-coded fallback
    return "I'm sorry, this feature is temporarily unavailable."

response = await model.run("Hello, how can you help me?")
print(response.content)
# Token usage, latency, and success tracked automatically — no tracker calls needed
```

**Python — retrieve multiple agent configs at once:**

```python
from ldai import AIAgentConfigRequest, AIAgentConfigDefault

agents = aiclient.agent_configs([
    AIAgentConfigRequest(key="summarizer-agent", default=AIAgentConfigDefault(enabled=False)),
    AIAgentConfigRequest(key="validator-agent",  default=AIAgentConfigDefault(enabled=False)),
], context)

summarizer = agents["summarizer-agent"]
validator  = agents["validator-agent"]
```

#### Reuse common prompt fragments with prompt snippets

If the user has the same persona, guardrails, or formatting instructions repeated across multiple configs, **prompt snippets** let them define the shared text once and reference it from any variation. When the snippet is updated, every variation that references it picks up the change.

Manage snippets via MCP when connected:

```
create-prompt-snippet:
  projectKey: "my-project"
  key: "company-tone"
  name: "Company tone"
  content: "Respond in a friendly, professional voice. Avoid jargon. Use plural 'we' when describing the company."

list-prompt-snippets / get-prompt-snippet / update-prompt-snippet / delete-prompt-snippet
  # for the rest of the lifecycle
```

Then reference the snippet inside a variation's `messages` or `instructions` so every config that needs that tone shares a single source. This pairs well with the migration stages below: when the audit reveals duplicate prompt fragments across call sites, extract them into snippets instead of copying the same string into each variation.

***

### NEXT STEP 7: Agent graphs (advanced)

**What this unlocks:** Define the topology of a multi-agent system — which agents hand off to which, and what data is passed. Change agent routing without touching code.

Docs: [https://docs.launchdarkly.com/home/ai-configs/agent-graphs](https://docs.launchdarkly.com/home/ai-configs/agent-graphs)\
Node.js example: `js-core/packages/sdk/server-ai/examples/agent-graph-traversal`

**Prerequisites:** Two or more agent-mode configs already created in LaunchDarkly.

**Prefer MCP when connected.** Agent graphs have full CRUD coverage in the AgentControl MCP — the agent can construct the graph, set the root node, draw the edges, and return the graph key without sending the user to the UI:

```
create-agent-graph:
  projectKey: "my-project"
  key: "support-triage"
  name: "Support triage"
  rootNodeKey: "router-agent"
  nodes:
    - key: "router-agent"
      configKey: "router-agent-config"
    - key: "billing-agent"
      configKey: "billing-agent-config"
    - key: "tech-agent"
      configKey: "tech-agent-config"
  edges:
    - from: "router-agent"
      to: "billing-agent"
    - from: "router-agent"
      to: "tech-agent"
```

Use `list-agent-graphs`, `get-agent-graph`, `update-agent-graph`, and `delete-agent-graph` for the rest of the lifecycle.

**UI fallback** (use only if MCP isn't available):

1. Left sidebar → **Configs** → **Agent graphs** → **Create agent graph**.
2. Add your agent configs as nodes. Assign one as the root.
3. Draw directed edges between nodes to define handoff order and optional handoff data.
4. Save and note the **graph key**.

**Python — retrieve and traverse the graph:**

```python
graph = aiclient.agent_graph(
    os.environ["LAUNCHDARKLY_GRAPH_KEY"],
    context,
)

def build_agent(node, execution_context):
    cfg = node.get_config()
    model_name = cfg.model.name if cfg.model else "gpt-5.4"
    return your_framework.Agent(
        name=node.get_key(),
        instructions=cfg.instructions or "",
        model=model_name,
    )

# Forward: root → leaf (use when framework builds parents before children)
graph.traverse(build_agent)

# Reverse: leaf → root (use when framework builds children before parents, e.g. LangGraph)
graph.reverse_traverse(build_agent)
```

***

### NEXT STEP 8: Run an experiment (advanced)

**What this unlocks:** Statistically validate that one prompt or model variation actually improves user behavior (clicks, conversions, task completions) compared to another — not just internal quality scores.

Docs: [https://docs.launchdarkly.com/home/ai-configs/experimentation](https://docs.launchdarkly.com/home/ai-configs/experimentation)\
Experimentation reference: [https://docs.launchdarkly.com/home/experimentation](https://docs.launchdarkly.com/home/experimentation)

**Step 1 — Add a second variation** (use `create-ai-config-variation` MCP, or **Variations** tab → + Add variation in the UI). Try a different model (e.g. `o4-mini` vs `gpt-5.4` for a cost/quality tradeoff) or a shorter/longer prompt.

**Step 2 — Instrument a user-behavior metric** in code:

```python
# Track a signal that shows the AI response was useful
ldclient.get().track("task-completed", context, metric_value=1)
```

**Step 3 — Configure and start the experiment.** Prefer MCP when connected:

```
create-experiment:
  projectKey: "my-project"
  key: "shorter-prompt-test"
  configKey: "chat-assistant"
  variationKeys: ["production-initial", "shorter-prompt"]
  metricKeys: ["task-completed"]
  primaryMetricKey: "task-completed"

start-experiment-iteration:
  projectKey: "my-project"
  experimentKey: "shorter-prompt-test"
```

Use `list-experiments`, `get-experiment`, and `update-experiment` to inspect or adjust an experiment. Results appear on the **Experimentation** tab as traffic accumulates.

**UI fallback** (use only if the experiment MCP tools aren't listed):

1. Go to your config → **Targeting** tab.
2. Set up a 50/50 percentage rollout between your two variations.
3. Click **Review and save** → select **Start experiment**.
4. Choose your metric(s) and set the primary goal.

**Note:** Guarded rollouts and experiments cannot run simultaneously on the same config. Use a guarded rollout to protect against quality regressions; use an experiment to measure user-facing impact.

***

### NEXT STEP 9: Guarded rollouts (advanced)

**What this unlocks:** When rolling out a new prompt or model, LaunchDarkly monitors your quality metrics in real time. If accuracy or relevance drops, the rollout pauses automatically before all users are affected.

Docs: [https://docs.launchdarkly.com/home/releases/guarded-rollouts](https://docs.launchdarkly.com/home/releases/guarded-rollouts)\
Targeting reference: [https://docs.launchdarkly.com/home/ai-configs/target](https://docs.launchdarkly.com/home/ai-configs/target)

**Prerequisites:** A judge attached to your config (NEXT STEP 2) so there are quality metrics to monitor.

**Prefer MCP when connected.** `start-guarded-rollout` configures the V2 measured rollout on the fallthrough rule in one call — pick the new variation, the metrics to monitor, the rollback thresholds, and start. `stop-guarded-rollout` ends it.

```
start-guarded-rollout:
  projectKey: "my-project"
  flagKey: "chat-assistant"
  env: "production"
  newVariationKey: "shorter-prompt"
  monitorMetrics: ["accuracy", "relevance"]
  rollbackOnRegression: true
```

**UI fallback** (use only if MCP isn't available):

1. Go to your config → **Targeting** tab.
2. Update the default rule to serve your new variation to an initial percentage of users (e.g., 10%).
3. Click **Review and save** → in the confirmation modal, select **Guarded rollout**.
4. Choose the metrics to monitor (judge scores work well here).
5. Set rollback thresholds and enable automatic rollback.
6. Start the rollout.

LaunchDarkly progressively increases traffic and monitors. If a regression is detected it pauses and sends a notification. No code changes are required.

***

### NEXT STEP 10: Governance and approvals (advanced)

**What this unlocks:** No prompt or model change can reach production without explicit approval from a designated reviewer — preventing unauthorized or accidental changes to AI behavior in production.

Docs: [https://docs.launchdarkly.com/home/releases/approval-config](https://docs.launchdarkly.com/home/releases/approval-config)\
Configs management: [https://docs.launchdarkly.com/home/ai-configs/manage](https://docs.launchdarkly.com/home/ai-configs/manage)

**In the LaunchDarkly UI:**

1. Go to **Account settings** → **Projects** → select your project → select your production environment.
2. Under **Approval settings**, enable approvals for config changes.
3. Set the minimum number of approvals required and (optionally) restrict who can approve.

Once configured, any variation or targeting change in that environment shows **Request approval** instead of **Review and save**. The change is queued until approved.

**No code changes are needed.** The SDK always evaluates whatever variation is in the current approved state.

***

### NEXT STEP 11: Complete the migration (existing-app users)

**What this unlocks:** Every hardcoded model name, prompt, parameter, and tool in the existing codebase becomes live config — editable in the LaunchDarkly UI, A/B testable, and guarded by rollout policies — without changing runtime behavior.

Migration guide: [https://docs.launchdarkly.com/guides/ai-configs/migrate-prompts](https://docs.launchdarkly.com/guides/ai-configs/migrate-prompts)

The migration runs in five ordered stages. Each stage is independently deployable. Read the full guide before starting.

***

#### Stage 1: Audit — find everything hardcoded

Scan the codebase and build an inventory. **Do not write code in this stage.** For every hit, record file, line range, and current value:

* **Model name literals:** `model="gpt-5.4"`, `model="claude-sonnet-4-6"`, `modelId="anthropic.claude-sonnet-4-6"`, etc.
* **Model parameters:** `temperature`, `max_tokens`, `top_p`, `max_completion_tokens`
* **System prompts / instructions:** full text of strings passed to `system=`, `systemPrompt:`, `instructions=`, or the first `{"role": "system", ...}` in a messages array
* **Tool definitions:** arguments to `tools=[...]`, `bind_tools(...)`, `ToolNode(...)` — flag each one
* **Template placeholders:** `.format()`, f-strings, JS template literals, `%(var)s`, `str.replace("__VAR__", ...)` — note each placeholder name, they become `{{ variable }}` in the config
* **Repeated prompt fragments:** identical chunks of system prompt or instructions that appear in 2+ call sites — note these for extraction into **prompt snippets** (one shared fragment, referenced from many variations) in Stage 2.

Also confirm:

* Does the app already initialize an `LDClient` for feature flags? If yes, **reuse it** — pass it to `LDAIClient()` / `initAi()` instead of creating a second one.
* Which config mode (completion or agent) matches how each call site works?

**Output of this stage:** a short audit manifest listing every hardcoded value and its location, plus a list of duplicate fragments to lift into snippets.

***

#### Stage 2: Wrap with identical fallback

For each call site in the manifest, create the config in LaunchDarkly (automated or manual), then update the code.

**Prefer Option A (MCP) when MCP is connected** — it keeps the user in the agent context and scales to dozens of call sites without manual UI work, which is the common case during a migration. Fall back to Option B (UI) only when MCP is unavailable or fails.

**Option A — LaunchDarkly MCP (preferred when connected)**

Use `setup-ai-config` with the exact values from your audit manifest. The `messages`/`instructions`/`parameters` fields are all optional — include only what you found hardcoded:

```
setup-ai-config:
  projectKey: "my-project"
  key: "chat-assistant"                      ← from audit manifest
  name: "Chat Assistant"
  mode: "completion"                         ← or "agent"
  variationKey: "production-initial"
  variationName: "Production (initial)"
  modelConfigKey: "OpenAI.gpt-5.4"           ← Provider.model-id format
  modelName: "gpt-5.4"
  messages:
    - role: "system"
      content: "You are a helpful assistant."  ← exact hardcoded value
  parameters:
    temperature: 0.7
    max_tokens: 2000
```

Then set the default targeting rule with `update-rollout`:

```
update-rollout:
  projectKey: "my-project"
  flagKey: "chat-assistant"     ← same as the config key
  env: "production"
  rolloutType: "variation"
  variationIndex: 0
```

**Option B — LaunchDarkly UI (always available)**

1. Left sidebar → **Create** → **AgentControl** → select mode → set name and key → **Create**
2. **Variations** tab → fill in the exact model, parameters, and system prompt or instructions from your audit manifest. Name the variation "Production (initial)".
3. **Targeting** tab → Default rule → serve the new variation → **Review and save**

***

**Replace the hardcoded values in code.** The code change is identical for both options:

**Python — completion mode:**

```python
from ldai import AICompletionConfigDefault, ModelConfig, LDMessage

FALLBACK = AICompletionConfigDefault(
    enabled=True,
    model=ModelConfig(name="gpt-5.4"),          # exact hardcoded value
    messages=[LDMessage(role="system", content="You are a helpful assistant.")],  # exact hardcoded prompt
)
config = aiclient.completion_config(
    os.environ["LAUNCHDARKLY_AI_CONFIG_KEY"],
    context,
    default=FALLBACK,
)
if not config.enabled:
    return "I'm sorry, this feature is temporarily unavailable."
```

**Python — agent mode:**

```python
from ldai import AIAgentConfigDefault, ModelConfig

FALLBACK = AIAgentConfigDefault(
    enabled=True,
    model=ModelConfig(name="gpt-5.4"),
    instructions="You are a helpful assistant.",  # exact hardcoded instructions
)
config = aiclient.agent_config(
    os.environ["LAUNCHDARKLY_AI_CONFIG_KEY"],
    context,
    default=FALLBACK,
)
if not config.enabled:
    return "I'm sorry, this feature is temporarily unavailable."
```

**Validate before continuing:** three paths must all work:

1. Normal path: response matches pre-migration output
2. Fallback path: unset the SDK key → fallback runs without error, same output
3. Live update: edit the variation in the LaunchDarkly UI, save, rerun → response reflects the change without redeploying

**Common pitfalls to check in the diff:**

* Fallback duplicates hardcoded values exactly (if it drifts, behavior changes when LaunchDarkly is unreachable)
* Provider call is structurally untouched — only its *inputs* (model, messages, tools) now come from `config`
* `completion_config` / `agent_config` is called **inside the request handler**, not at module level at startup

***

#### Stage 3: Move tools (optional — skip if no function calling)

If the app uses tool definitions:

**Step 1: Extract each tool's JSON schema programmatically**

* LangChain `@tool` functions: `my_tool.args_schema.model_json_schema()`
* Plain callables: `StructuredTool.from_function(my_fn).args_schema.model_json_schema()`
* SDK-native tool definitions: the JSON schema is usually already present in the definition object

The schema must be a **raw JSON Schema object** (`{"type": "object", "properties": {...}}`). Do NOT wrap it in the OpenAI function-calling format.

**Step 2: Create the tool in LaunchDarkly** — prefer MCP when connected so you can register all the tools in one pass without context-switching to the UI.

*Option A — MCP (preferred when connected):*

```
create-ai-tool:
  projectKey: "my-project"
  key: "get-weather"
  description: "Get the current weather for a location"
  schema:
    type: "object"
    properties:
      location:
        type: "string"
        description: "City and state, e.g. 'San Francisco, CA'"
    required: ["location"]
```

*Option B — UI (always available):* AgentControl → Library → Tools tab → Add tool → paste schema

**Step 3: Attach the tool to your variation** — prefer MCP when connected.

*Option A — MCP (preferred when connected):*

```
update-ai-config-variation:
  projectKey: "my-project"
  configKey: "chat-assistant"
  variationKey: "production-initial"
  tools:
    - key: "get-weather"
      version: 1
```

*Option B — UI (always available):* open the variation editor → **+ Attach tools** → select the tool

**Step 4: Update code to read tools from the config**

Update the code to read `config.tools` at call time instead of the hardcoded tool list. The tool schema LaunchDarkly returns is flat; each provider needs a conversion at the boundary — consult the provider guide for the exact conversion.

If you use a LangGraph `StateGraph` with a `TOOLS` list, update **both** `.bind_tools(TOOLS)` **and** `ToolNode(TOOLS)`. Updating only one causes the LLM and executor to use different tool sets.

***

#### Stage 4: Instrument the tracker correctly

The integration in Phase 2 may have added a tracker — verify it follows the one-tracker-per-turn rule, then extend it:

**Rules:**

* Call `tracker = config.create_tracker()` **once per user turn** (full request-response cycle, including retries and agent loop iterations) — reuse the same tracker object throughout the turn
* Never share one tracker across unrelated turns; never create a new tracker per loop iteration
* At-most-once methods (`track_duration`, `track_tokens`, `track_success`, `track_error`) fire once per tracker — a second call logs a warning and no-ops

**For agent loops (LangGraph ReAct, custom tool-call loops):**

Do NOT wrap each LLM call in `track_metrics_of_async` inside the loop. Instead:

```python
# At turn start (e.g., entry node)
tracker = config.create_tracker()
total_tokens = TokenUsage(input=0, output=0, total=0)

# Inside the loop — accumulate tool calls and token counts
tracker.track_tool_calls(tool_calls)
# accumulate token usage locally

# At turn end (terminal node, after loop exits)
tracker.track_tokens(total_tokens)
tracker.track_success()   # or tracker.track_error()
```

**For single provider calls (completion mode, standard usage):**

```python
from ldai_openai import get_ai_metrics_from_response

tracker = config.create_tracker()
response = tracker.track_metrics_of(
    get_ai_metrics_from_response,
    lambda: openai_client.chat.completions.create(model=..., messages=...),
)
# track_metrics_of handles duration + tokens + success/error automatically
```

**For non-OpenAI providers** — write a small extractor (usually under 10 lines) and use `track_metrics_of`:

```python
from ldai.providers.types import LDAIMetrics
from ldai.tracker import TokenUsage

def anthropic_extractor(response) -> LDAIMetrics:
    return LDAIMetrics(
        success=response.stop_reason == "end_turn",
        tokens=TokenUsage(
            input=response.usage.input_tokens,
            output=response.usage.output_tokens,
            total=response.usage.input_tokens + response.usage.output_tokens,
        ),
    )

tracker = config.create_tracker()
response = tracker.track_metrics_of(
    anthropic_extractor,
    lambda: anthropic_client.messages.create(...),
)
```

***

#### Stage 5: Attach evaluations

Three paths — pick one based on mode and rollout stage:

| Path                      | When to use                                          | Supports agent mode  |
| ------------------------- | ---------------------------------------------------- | -------------------- |
| Offline evaluation        | Prove new variation matches baseline before rollout  | Yes                  |
| UI-attached judges        | Continuous live scoring on sampled requests, no code | Completion mode only |
| Programmatic direct-judge | Per-request scoring from application code            | Yes                  |

Start with **offline evaluation** — you already have the hardcoded baseline to compare against. Run the LLM Playground with your dataset to get a pre-release quality signal.

Then wire judges or experiments from the next-steps menu (options 1 and 2).

***

**Docs:** [https://docs.launchdarkly.com/guides/ai-configs/migrate-prompts](https://docs.launchdarkly.com/guides/ai-configs/migrate-prompts)

***

### Guidance for all next steps

* **For UI-only topics** (account-level approval settings configuration, the interactive LLM Playground browser experience): walk through the UI steps and answer questions. Do not write code unless asked. **The UI-only set is shrinking as new MCP tools ship — always check the live `tools/list` rather than assuming a topic is UI-only.** See the [MCP capability map](#mcp-capability-map) for the current reference and the dynamic-discovery directive at the top of the prompt.
* **For code topics** (judges in code, traces, agent graphs, migration): read the relevant docs URL first, then write the minimal change needed — do not rewrite the entire integration.
* **For LaunchDarkly configuration tasks that MCP supports** (creating configs, variations, tools, setting targeting, getting SDK keys, submitting approval requests): **always prefer MCP when it's connected** — keep the user inside the agent context instead of sending them to the UI. Tell the user what you did via MCP so they can verify in the UI later if they want. Fall back to UI instructions only if MCP is not connected or a call fails. See the [MCP capability map](#mcp-capability-map).
* **Always tailor examples** to the user's language (Python or Node.js) and config mode (completion or agent).
* **After any topic is complete**, re-offer the next-steps menu. When you do, acknowledge what they just accomplished, reference which steps they've already done, and actively recommend the most logical next step rather than simply listing all options again. The goal is to guide the user progressively through the full product — monitoring → judging → experiments → guarded rollouts → governance — so they understand and use each layer, not just the first one they try.
* **Keep the momentum going.** As users complete more steps, nudge them toward the parts they haven't explored yet. A user who has added a judge should be encouraged to run their first eval or set up a guarded rollout. A user who has viewed monitoring data should be encouraged to add user satisfaction tracking. Frame each suggestion around what it unlocks for them specifically.
* **LaunchDarkly configuration without MCP:** The LaunchDarkly UI is always the reliable fallback — it requires no setup and supports every operation covered in this prompt. If the user has an API token, they can also use the REST API (`https://app.launchdarkly.com/api/v2`, reference: [https://apidocs.launchdarkly.com/tag/AI-configs](https://apidocs.launchdarkly.com/tag/AI-configs)). Never block progress on MCP availability.
* **Set delay expectations whenever you point users at a dashboard.** Monitoring data, traces, and judge scores typically take **1–2 minutes** (sometimes longer for first scores) to populate after the triggering AI call. Tell the user this *before* they look — it prevents the most common "the dashboard is empty, what's wrong?" troubleshooting cycle.

