import sys
import time
sys.path.insert(0, ".")
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json as _json

import scripts.import_graph_audit as A

root = Path(".").resolve()
print("=== phase 1: populate ===", flush=True)
t0 = time.time()
A._populate_index(root, A._PROD_SKIP)
modules: dict[str, Path] = dict(A._MODULE_INDEX)
print("populate:", round(time.time() - t0, 2), "s  modules:", len(modules), flush=True)

print("=== phase 2: lazy_map ===", flush=True)
t0 = time.time()
lazy = A.load_lazy_tools_map(root)
print("lazy_map:", round(time.time() - t0, 2), "s  entries:", len(lazy), flush=True)

print("=== phase 3: audit ===", flush=True)
t0 = time.time()
broken = []
for mod in sorted(A._MODULE_INDEX):
    broken.extend(A.audit_module(root, mod, lazy))
print("audit:", round(time.time() - t0, 2), "s  broken:", len(broken), flush=True)

print("=== phase 4: edges ===", flush=True)
t0 = time.time()
edges = A.build_internal_edges(root, lazy)
print("edges:", round(time.time() - t0, 2), "s", flush=True)

print("=== phase 5: live closure ===", flush=True)
t0 = time.time()
entry_roots = [A.path_to_module(root, (root / ep).resolve()) for ep in A._DEFAULT_ENTRYPOINTS if (root / ep).exists()]
live = A.reachable_closure(edges, entry_roots)
print("closure:", round(time.time() - t0, 2), "s  live:", len(live), flush=True)
for rec in broken:
    rec["live"] = rec.get("importer") in live

print("=== phase 6: report+json+print (reuses globals) ===", flush=True)
t0 = time.time()
orphans = sorted((m for m in modules if m not in live), key=lambda m: (m.split(".")[0], m))
live_broken = [b for b in broken if b.get("live")]
report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "root": str(root),
    "entrypoints": entry_roots,
    "stats": {
        "total_modules": len(modules),
        "reachable_modules": len(live),
        "orphan_modules": len(orphans),
        "broken_imports": len(broken),
        "live_broken_imports": len(live_broken),
    },
    "broken_imports": broken,
    "orphans": [{"module": m, "lines": A._MODULE_LINES.get(m, 0)} for m in orphans],
}
t_json = time.time()
js = _json.dumps(report, indent=2)
Path("_audit_baseline.json").write_text(js, encoding="utf-8")
print("   report+json+write:", round(time.time() - t_json, 2), "s  json_bytes:", len(js), flush=True)
shown = live_broken  # --live-only style; print a bounded sample
print("   broken-to-print:", len(broken), flush=True)
for b in broken[:5]:
    print("  sample", b.get("importer"), b.get("reason"), flush=True)
top = Counter(m.split(".")[0] for m in orphans)
print("   orphan pkgs:", len(top), flush=True)
print("report_total:", round(time.time() - t0, 2), "s", flush=True)
print("=== DONE ===", flush=True)




