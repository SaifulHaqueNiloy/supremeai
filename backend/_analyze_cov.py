import json

data = json.load(open("coverage.json"))
totals = data.get("totals", {})

files = data.get("files", {})
file_list = []
for name, info in files.items():
    missing = info.get("missing_lines", [])
    stmts = info.get("summary", {}).get("num_statements", 0)
    covered = info.get("summary", {}).get("covered_lines", 0)
    pct = info.get("summary", {}).get("percent_covered", 0)
    file_list.append((name, len(missing), stmts, covered, pct))

file_list.sort(key=lambda x: x[1], reverse=True)
for name, missing, stmts, covered, pct in file_list[:20]:
    pass
