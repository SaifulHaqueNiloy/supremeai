import json
from collections import defaultdict

data = json.load(open("coverage.json"))
files = data.get("files", {})

# Group by top-level package
pkg_lines = defaultdict(lambda: {"covered": 0, "total": 0})
pkg_files = defaultdict(set)
for fpath, finfo in files.items():
    parts = fpath.replace("\\", "/").split("/")
    pkg = parts[0] if parts else "other"
    pkg_lines[pkg]["total"] += finfo.get("num_statements", 0)
    pkg_lines[pkg]["covered"] += finfo.get("covered_lines", 0)
    pkg_files[pkg].add(fpath)

total_covered = 0
total_stmts = 0
for pkg in sorted(pkg_lines.keys()):
    info = pkg_lines[pkg]
    pct = (info["covered"] / info["total"] * 100) if info["total"] else 0
    line_str = f"{info['covered']:>5d}/{info['total']:>5d}"
    total_covered += info["covered"]
    total_stmts += info["total"]

overall = (total_covered / total_stmts * 100) if total_stmts else 0

file_pcts = []
for fpath, finfo in files.items():
    if finfo.get("num_statements", 0) > 0:
        pct = finfo["covered_lines"] / finfo["num_statements"] * 100
        file_pcts.append((pct, finfo["num_statements"], finfo["missing_lines"], fpath))
file_pcts.sort()
for pct, stmts, missing, fpath in file_pcts[:30]:
    pass

file_missing = []
for fpath, finfo in files.items():
    if finfo.get("num_statements", 0) > 0:
        missing_count = finfo["num_statements"] - finfo["covered_lines"]
        pct = finfo["covered_lines"] / finfo["num_statements"] * 100
        file_missing.append((missing_count, pct, finfo["num_statements"], fpath))
file_missing.sort(reverse=True)
for missing_count, pct, stmts, fpath in file_missing[:30]:
    pass
