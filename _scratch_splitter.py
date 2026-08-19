import ast, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC_PATH = r"f:\supremeai backup\backend\tests\test_mcp_servers_integration.py"
OUT_DIR = r"f:\supremeai backup\backend\tests\mcp"
os.makedirs(OUT_DIR, exist_ok=True)
src = open(SRC_PATH, encoding="utf-8").read()
lines = src.splitlines()
tree = ast.parse(src)

def seg(a, b):
    return "\n".join(lines[a-1:b])

def cls_src(node):
    start = min([d.lineno for d in node.decorator_list], default=node.lineno) if getattr(node, "decorator_list", None) else node.lineno
    return seg(start, node.end_lineno)

def method_src(m):
    start = min([d.lineno for d in m.decorator_list], default=m.lineno) if getattr(m, "decorator_list", None) else m.lineno
    return seg(start, m.end_lineno)

classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
valid_cls = classes["TestInputValidation"]

DOM = {"cloud_deploy": "cloud", "github_cicd": "github", "supabase": "supabase", "workspace": "workspace"}
def method_domain(m):
    mods = set()
    for node in ast.walk(m):
        if isinstance(node, ast.ImportFrom) and node.module and "tools.mcp" in node.module:
            last = node.module.split(".")[-1]
            for d in DOM:
                if d in last:
                    mods.add(DOM[d])
    return ",".join(sorted(mods)) if mods else "NONE"

validation_by_domain = {}
for m in valid_cls.body:
    if not isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    validation_by_domain.setdefault(method_domain(m), []).append(method_src(m))

fix = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "mock_env_vars")
conftest = '''# backend/tests/mcp/conftest.py
# বাংলা মন্তব্য: MCP টেস্ট-সাবপ্যাকেজের শেয়ার্ড ফিক্সচার (test_mcp_servers_integration.py থেকে স্থানান্তরিত)
import pytest

''' + seg(fix.lineno, fix.end_lineno) + "\n"
with open(os.path.join(OUT_DIR, "conftest.py"), "w", encoding="utf-8", newline="\n") as f:
    f.write(conftest)
print("WROTE conftest.py")

HEADER_COMMON = '''# backend/tests/mcp/{fname}
# বাংলা মন্তব্য: {desc}
# --- test_mcp_servers_integration.py থেকে স্প্লিট করা হয়েছে ---

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError
'''

def write(fname, desc, body_parts, extra_imports=""):
    header = HEADER_COMMON.format(fname=fname, desc=desc)
    if extra_imports:
        header = header.replace("from pydantic import ValidationError\n",
                                "from pydantic import ValidationError\n" + extra_imports)
    content = header + "\n\n\n" + "\n\n\n".join(body_parts) + "\n"
    with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"WROTE {fname}  ({content.count(chr(10))} lines)")

cloud_parts = [cls_src(classes["TestCloudDeployMCP"]), cls_src(classes["TestCloudDeployMCPExtended"])] + validation_by_domain.get("cloud", [])
write("test_cloud_deploy_mcp.py", "Cloud Deploy MCP (Render/Railway/Oracle) টেস্ট", cloud_parts)

gh_parts = [cls_src(classes["TestGithubCICDMCP"]), cls_src(classes["TestGithubCICDMCPExtended"])] + validation_by_domain.get("github", [])
write("test_github_cicd_mcp.py", "GitHub CICD MCP টেস্ট", gh_parts)

sb_parts = [cls_src(classes["TestSupabaseMCP"]), cls_src(classes["TestSupabaseMCPExtended"])] + validation_by_domain.get("supabase", [])
write("test_supabase_mcp.py", "Supabase MCP টেস্ট", sb_parts)

ws_parts = [cls_src(classes["TestWorkspaceMCP"]), cls_src(classes["TestWorkspaceMCPExtended"])] + validation_by_domain.get("workspace", [])
write("test_workspace_mcp.py", "Workspace MCP টেস্ট", ws_parts)

proto_parts = [cls_src(classes["TestMCPServerSync"]), cls_src(classes["TestHelperFunctions"])]
write("test_protocol_sync.py", "MCP সার্ভার সিকনেশন/সিঙ্ক ও হেল্পার টেস্ট", proto_parts, extra_imports="import importlib\n")

for d in validation_by_domain:
    if d not in ("cloud", "github", "supabase", "workspace"):
        write(f"test_validation_{d}.py", f"validation ({d})", validation_by_domain[d])

# ---- LOSS-LESS VERIFICATION ----
def count_tests(path):
    t = ast.parse(open(path, encoding="utf-8").read())
    return sum(1 for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_"))

orig = count_tests(SRC_PATH)
total_new = 0
for fn in os.listdir(OUT_DIR):
    if fn.endswith(".py") and fn != "conftest.py":
        total_new += count_tests(os.path.join(OUT_DIR, fn))
print(f"\nVERIFY: original test_ methods = {orig}, new files total = {total_new}")
print("LOSS_LESS" if orig == total_new else "MISMATCH !!")