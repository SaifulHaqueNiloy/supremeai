import ast, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
src = open(r"f:\supremeai backup\backend\tests\test_mcp_servers_integration.py", encoding="utf-8").read()
lines = src.splitlines()
tree = ast.parse(src)
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        start = node.lineno
        end = getattr(node, "end_lineno", start)
        nmethods = sum(1 for s in node.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)))
        print(f"CLASS {node.name} L{start}-L{end} methods={nmethods}")
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print(f"FUNC  {node.name} L{node.lineno}-L{getattr(node,'end_lineno',node.lineno)}")
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        pass
print("TOTAL_LINES", len(lines))