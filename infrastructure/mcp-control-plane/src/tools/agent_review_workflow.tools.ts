import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { env } from "../lib/env.js";
import { httpRequest, bearerAuth } from "../lib/http.js";

const MAX_PROMPT_LENGTH = 50_000;
const MAX_CONTEXT_LENGTH = 200_000;

const contextSchema = z.record(z.string(), z.unknown()).optional();

async function backendRequest<T>(path: string, body?: unknown): Promise<T> {
  if (!env.backendUrl) throw new Error("SUPREMEAI_BACKEND_URL is not configured");
  const headers = env.backendServiceToken ? bearerAuth(env.backendServiceToken) : {};
  const response = await httpRequest<T>(`${env.backendUrl.replace(/\/$/, "")}${path}`, {
    method: body ? "POST" : "GET",
    headers,
    body,
    timeoutMs: 90_000,
    retries: 0,
  });
  if (!response.ok) throw new Error(`Backend returned HTTP ${response.status}`);
  return response.data;
}

export async function registerAgentReviewWorkflowTools(server: McpServer): Promise<void> {
  server.tool(
    "agent_review_workflow.execute",
    "Execute the reusable Agent Review Workflow. Provider and model selection are resolved by runtime configuration.",
    {
      prompt: z.string().min(1).max(MAX_PROMPT_LENGTH),
      language: z.string().min(1).max(64).default("python"),
      context: contextSchema,
    },
    async ({ prompt, language, context }) => {
      try {
        const serializedContext = JSON.stringify(context ?? {});
        if (serializedContext.length > MAX_CONTEXT_LENGTH) {
          throw new Error("Workflow context exceeds the configured size limit");
        }
        const result = await backendRequest("/api/v1/agent_review_workflow/execute", {
          prompt,
          language,
          ...((context ?? {}) as Record<string, unknown>),
        });
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return { isError: true, content: [{ type: "text", text: `Error: ${(err as Error).message}` }] };
      }
    },
  );

  server.tool(
    "agent_review_workflow.status",
    "Report runtime availability of the Agent Review Workflow and its configured capabilities.",
    {},
    async () => {
      try {
        const result = await backendRequest("/api/v1/agent_review_workflow/status");
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return { isError: true, content: [{ type: "text", text: `Error: ${(err as Error).message}` }] };
      }
    },
  );
}
