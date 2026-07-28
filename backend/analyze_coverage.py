"""Analyze coverage.json and identify high-priority files needing tests."""

import json

with open("coverage.json") as f:
    data = json.load(f)

files = data["files"]

# High-priority targets from TEST_COVERAGE_IMPROVEMENT_PLAN.md
targets = [
    "api/routes/__init__.py",
    "core/evolution/daily_learner.py",
    "tools/sso_integrator.py",
    "api/routes/tenant_admin.py",
    "core/cache/multi_layer_cache.py",
    "services/memory_service.py",
    "tools/knowledge/local_search_rag.py",
    "tools/seed_database.py",
    "tools/self_planner.py",
    "services/rider_tracker.py",
    "core/llm_router.py",
    "tools/security_tools/multi_account_rotator.py",
    "core/queue/task_queue_enhanced.py",
    "api/routes/browser.py",
    "core/tier8/self_improvement_agent.py",
    "tools/learning/style_learner.py",
    "api/routes/meta_ai.py",
    "core/security/input_sanitizer.py",
    "core/security/secret_vault.py",
    "core/security/audit_logger.py",
    "core/security/origin_validator.py",
    "core/security/autonoguard_middleware.py",
    "core/cache/redis_manager.py",
    "core/resilience/circuit_breaker.py",
    "core/security/auth_middleware.py",
    "core/security/rbac.py",
    "core/security/honeypot_middleware.py",
    "core/security/prompt_firewall.py",
    "core/security/guardian_ai.py",
    "core/security/compliance_bot.py",
]

if __name__ == "__main__":
    print("=" * 80)
    print("HIGH-PRIORITY TARGET COVERAGE STATUS")
    print("=" * 80)
    for t in targets:
        if t in files:
            s = files[t]["summary"]
            status = "LOW" if s["percent_covered"] < 50 else "MEDIUM" if s["percent_covered"] < 80 else "GOOD"
            print(f"  {status:6s} | {s['percent_covered']:5.1f}% | {s['num_statements']:5d} stmts | {t}")
        else:
            print(f"  MISS  |  N/A  |  N/A  | {t}")

    print()
    print("=" * 80)
    print("ALL FILES WITH < 30% COVERAGE (> 10 statements)")
    print("=" * 80)
    low_files = []
    for name, info in files.items():
        s = info["summary"]
        if s["num_statements"] > 10 and s["percent_covered"] < 30:
            low_files.append((name, s["percent_covered"], s["num_statements"]))

    for name, pct, stmts in sorted(low_files, key=lambda x: x[1]):
        print(f"  {pct:5.1f}% | {stmts:5d} stmts | {name}")

    print(f"\nTotal low-coverage files: {len(low_files)}")
