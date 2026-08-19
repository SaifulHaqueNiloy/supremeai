import ast, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
src = open(r"f:\supremeai backup\backend\tests\test_mcp_servers_integration.py", encoding="utf-8").read()
tree = ast.parse(src)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TestInputValidation")

DOM = {"cloud_deploy":"cloud", "github_cicd":"github", "supabase":"supabase", "workspace":"workspace"}
counts = {}
for m in cls.body:
    if not isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    mods = set()
    for node in ast.walk(m):
        if isinstance(node, ast.ImportFrom) and node.module and "tools.mcp" in node.module:
            last = node.module.split(".")[-1]
            for d in DOM:
                if d in last:
                    mods.add(DOM[d])
    key = ",".join(sorted(mods)) if mods else "NONE"
    counts[key] = counts.get(key, 0) + 1
    print(f"  M:{m.lineno}-{m.end_lineno} {m.name:45s} -> {key}")
print("SUMMARY", counts)