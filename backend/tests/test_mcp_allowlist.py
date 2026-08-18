from core.mcp_allowlist import MCPAllowlist, get_mcp_servers


def test_get_mcp_servers_shape():
    servers = get_mcp_servers()
    assert "github" in servers
    assert "slack" in servers
    assert "filesystem" in servers
    assert "playwright" in servers
    assert "context7" in servers
    assert "mcp-deepwiki" in servers
    assert "github-npx" in servers
    for _name, config in servers.items():
        assert "command" in config
        assert "allowed_tools" in config
        assert "allowed_paths" in config


def test_validate_server_allowed():
    result = MCPAllowlist.validate_server("github")
    assert result["allowed"] is True
    assert result["server"] == "github"
    assert "search_repositories" in result["tools"]


def test_validate_new_servers():
    # Playwright validation
    pw_res = MCPAllowlist.validate_server("playwright")
    assert pw_res["allowed"] is True
    assert "navigate" in pw_res["tools"]
    assert "screenshot" in pw_res["tools"]

    # Context7 validation
    ctx_res = MCPAllowlist.validate_server("context7")
    assert ctx_res["allowed"] is True
    assert "query_docs" in ctx_res["tools"]

    # DeepWiki validation
    wiki_res = MCPAllowlist.validate_server("mcp-deepwiki")
    assert wiki_res["allowed"] is True
    assert "search_wiki" in wiki_res["tools"]

    # GitHub NPX validation
    gh_res = MCPAllowlist.validate_server("github-npx")
    assert gh_res["allowed"] is True
    assert "create_pull_request" in gh_res["tools"]


def test_validate_server_denied():
    result = MCPAllowlist.validate_server("nonexistent")
    assert result["allowed"] is False
    assert result["reason"] == "unknown mcp server"


def test_allowed_tools_all_granted():
    result = MCPAllowlist.allowed_tools("github", ["search_repositories", "get_file_contents"])
    assert result["allowed"] is True
    assert result["denied"] == []


def test_allowed_tools_partial_denied():
    result = MCPAllowlist.allowed_tools("github", ["search_repositories", "evil_tool"])
    assert result["allowed"] is False
    assert "evil_tool" in result["denied"]
    assert "search_repositories" in result["allowed_tools"]


def test_allowed_tools_server_denied():
    result = MCPAllowlist.allowed_tools("nonexistent", ["any_tool"])
    assert result["allowed"] is False
    assert result["denied"] == ["any_tool"]

