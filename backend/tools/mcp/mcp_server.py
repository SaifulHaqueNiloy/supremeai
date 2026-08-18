# backend/tools/mcp_server.py
import asyncio
import json

from loguru import logger
from mcp import types
from mcp.server import Server

from tools.graph_service import GraphService
from tools.mcp.mcp_mesh_engine import mesh_executor, mesh_registry

# বাংলা মন্তব্য: নলেজ গ্রাফ ও অ্যাডাপ্টিভ মেশের জন্য একটি অফিসিয়াল MCP সার্ভার ইনিশিয়ালাইজ করা হচ্ছে
app = Server("supremeai-knowledge-graph")
graph_service = GraphService()


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """বাংলা মন্তব্য: এআই এজেন্টের কাছে এভেইলেবল গ্রাফ ও অ্যাডাপ্টিভ মেশ টুলসগুলোর তালিকা প্রকাশ করবে।"""
    return [
        types.Tool(
            name="get_skill_dependencies",
            description="Exposes the entire dependency and connection graph of SupremeAI skills.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="find_optimal_learning_path",
            description="Finds the shortest, optimized chain between two complex skills.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_skill": {
                        "type": "string",
                        "description": "The starting skill name",
                    },
                    "end_skill": {
                        "type": "string",
                        "description": "The target skill name",
                    },
                },
                "required": ["start_skill", "end_skill"],
            },
        ),
        types.Tool(
            name="semantic_tool_search",
            description="Performs $0-cost semantic vector search to find only relevant tools for a user prompt.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user query or intention to find tools for",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of tools to return",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="synthesize_custom_tool",
            description="JIT synthesizes, validates, and registers a brand new Python MCP tool on the fly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique tool name"},
                    "code": {"type": "string", "description": "Python source code defining the entrypoint function"},
                    "entrypoint": {"type": "string", "description": "Function name to call"},
                    "description": {"type": "string", "description": "Tool functionality description"},
                },
                "required": ["name", "code", "entrypoint", "description"],
            },
        ),
        types.Tool(
            name="execute_smart_tool",
            description="Executes an MCP tool with automated argument sanitization and self-healing fallback.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "The name of the tool to execute"},
                    "arguments": {"type": "object", "description": "Arguments dictionary for the tool"},
                },
                "required": ["tool_name"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """বাংলা মন্তব্য: এআই এজেন্টের রিকোয়েস্ট অনুযায়ী নির্দিষ্ট গ্রাফ ও মেশ কোয়েরি এক্সিকিউট করে কনটেক্সট রিটার্ন করবে।"""
    if not arguments:
        arguments = {}

    try:
        if name == "get_skill_dependencies":
            # ডাটাবেস সেশন বা মক ডেটা থেকে কনটেক্সট গ্যাদারিং
            if graph_service.dry_run:
                graph_data = {
                    "status": "dry-run",
                    "nodes": ["Python", "FastAPI", "Redis"],
                }
            else:
                async with graph_service.driver.session() as session:
                    result = await session.run("MATCH (n:Skill) RETURN n.name AS name LIMIT 50")
                    records = await result.data()
                    graph_data = {"nodes": [r["name"] for r in records]}

            return [
                types.TextContent(
                    type="text",
                    text=f"SupremeAI Skills Graph Context:\n{json.dumps(graph_data, indent=2)}",
                )
            ]

        elif name == "find_optimal_learning_path":
            start = arguments.get("start_skill")
            end = arguments.get("end_skill")

            path = await graph_service.get_skill_path(start, end)
            return [
                types.TextContent(
                    type="text",
                    text=f"Optimal execution path from {start} to {end}:\n{' -> '.join(path) if path else 'No path found.'}",
                )
            ]

        elif name == "semantic_tool_search":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 3)
            matched = mesh_registry.router.search_relevant_tools(query=query, top_k=int(top_k))
            return [
                types.TextContent(
                    type="text",
                    text=f"Semantic Tool Search Results for '{query}':\n{json.dumps(matched, indent=2)}",
                )
            ]

        elif name == "synthesize_custom_tool":
            tool_name = arguments.get("name", "")
            code = arguments.get("code", "")
            entrypoint = arguments.get("entrypoint", "")
            desc = arguments.get("description", "")
            res = mesh_registry.synthesize_tool(name=tool_name, code=code, entrypoint=entrypoint, description=desc)
            return [
                types.TextContent(
                    type="text",
                    text=f"JIT Synthesis Result:\n{json.dumps(res, indent=2)}",
                )
            ]

        elif name == "execute_smart_tool":
            target_tool = arguments.get("tool_name", "")
            target_args = arguments.get("arguments", {})
            exec_res = await mesh_executor.execute(tool_name=target_tool, arguments=target_args)
            return [
                types.TextContent(
                    type="text",
                    text=f"Smart Tool Execution Result:\n{json.dumps(exec_res, indent=2)}",
                )
            ]

        else:
            raise ValueError(f"Unknown MCP tool: {name}")

    except Exception as e:
        logger.error(f"MCP Server execution error: {e}")
        return [types.TextContent(type="text", text=f"Error gathering graph context: {e!s}")]


async def main():
    # Stdio ট্রান্সপোর্টের মাধ্যমে সার্ভারটি রান করানো (Standard Input/Output)
    from mcp.server.stdio import stdio_server

    logger.info("Starting SupremeAI MCP Graph Server over Stdio...")
    async with stdio_server() as (read_stream, write_server):
        await app.run(read_stream, write_server, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
