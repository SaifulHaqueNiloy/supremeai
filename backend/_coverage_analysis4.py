import json
from collections import defaultdict

data = json.load(open("coverage.json"))
files = data.get("files", {})


def get_statements(finfo):
    return finfo.get("summary", {}).get("num_statements", 0)


def get_covered(finfo):
    return finfo.get("summary", {}).get("covered_lines", 0)


def normalize_path(p):
    p = p.replace("\\", "/")
    if ":" in p:
        parts = p.split("/")
        for i, part in enumerate(parts):
            if part == "supremeai_2.0":
                return "/".join(parts[i + 1 :])
        return p
    return p


pkg_lines = defaultdict(lambda: {"covered": 0, "total": 0})
for fpath, finfo in files.items():
    norm = normalize_path(fpath)
    parts = norm.split("/")
    pkg = parts[0] if parts else "other"
    pkg_lines[pkg]["total"] += get_statements(finfo)
    pkg_lines[pkg]["covered"] += get_covered(finfo)

total_covered = 0
total_stmts = 0
for pkg in sorted(pkg_lines.keys()):
    info = pkg_lines[pkg]
    pct = (info["covered"] / info["total"] * 100) if info["total"] else 0
    total_covered += info["covered"]
    total_stmts += info["total"]

overall = (total_covered / total_stmts * 100) if total_stmts else 0

zero_coverage = []
for fpath, finfo in files.items():
    stmts = get_statements(finfo)
    if stmts > 0 and get_covered(finfo) == 0:
        norm = normalize_path(fpath)
        zero_coverage.append((stmts, norm))
zero_coverage.sort(reverse=True)
for _stmts, _fpath in zero_coverage[:25]:
    pass

needs_work = []
for fpath, finfo in files.items():
    stmts = get_statements(finfo)
    if stmts > 0:
        covered = get_covered(finfo)
        pct = covered / stmts * 100
        if pct < 50:
            norm = normalize_path(fpath)
            missing = stmts - covered
            needs_work.append((missing, pct, stmts, covered, norm))
needs_work.sort(reverse=True)
for _missing, _pct, _stmts, _covered, _fpath in needs_work[:30]:
    pass

medium = []
for fpath, finfo in files.items():
    stmts = get_statements(finfo)
    if stmts > 0:
        covered = get_covered(finfo)
        pct = covered / stmts * 100
        if 50 <= pct < 80:
            norm = normalize_path(fpath)
            missing = stmts - covered
            medium.append((missing, pct, stmts, covered, norm))
medium.sort(reverse=True)
for _missing, _pct, _stmts, _covered, _fpath in medium[:20]:
    pass

t = data["totals"]

target_pct = 90.0
target_lines = int(t["num_statements"] * target_pct / 100)
additional_needed = target_lines - t["covered_lines"]
