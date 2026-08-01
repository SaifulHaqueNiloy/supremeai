import json
from collections import defaultdict

data = json.load(open("coverage.json"))
files = data.get("files", {})

# Group by top-level package
pkg_lines = defaultdict(lambda: {"covered": 0, "total": 0})
for fpath, finfo in files.items():
    parts = fpath.replace("\\", "/").split("/")
    pkg = parts[0] if parts else "other"
    pkg_lines[pkg]["total"] += finfo.get("num_statements", 0)
    pkg_lines[pkg]["covered"] += finfo.get("covered_lines", 0)

for pkg in sorted(pkg_lines.keys()):
    info = pkg_lines[pkg]
    pct = (info["covered"] / info["total"] * 100) if info["total"] else 0

file_pcts = []
for fpath, finfo in files.items():
    if finfo.get("num_statements", 0) > 0:
        pct = finfo["covered_lines"] / finfo["num_statements"] * 100
        file_pcts.append((pct, finfo["num_statements"], fpath))
file_pcts.sort()
for _pct, _stmts, _fpath in file_pcts[:20]:
    pass

file_missing = []
for fpath, finfo in files.items():
    if finfo.get("num_statements", 0) > 0:
        missing = finfo["num_statements"] - finfo["covered_lines"]
        pct = finfo["covered_lines"] / finfo["num_statements"] * 100
        file_missing.append((missing, pct, finfo["num_statements"], fpath))
file_missing.sort(reverse=True)
for _missing, _pct, _stmts, _fpath in file_missing[:20]:
    pass
