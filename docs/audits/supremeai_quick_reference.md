# ⚡ Quick Reference - What to Do NOW

## 🔥 TOP 5 IMMEDIATE ACTIONS (Highest Impact)

### 1. MERGE: scripts/devops/ (12 files → 3)
```bash
# Create these 3 new files:
scripts/devops/devops_audit_suite.py     # Merge: bug_prophet + refactor_wiz + generate_modular_audits + run_local_audit
scripts/devops/devops_ai_scribe.py       # Merge: ai_scribe_historian + ask_scribe  
scripts/devops/devops_security_scan.py   # Merge: fast_secret_scan + secret_scan_ci + wire_error_bus

# Delete 9 old files after merge
```

### 2. MERGE: scripts/backup/ (7 files → 2)
```bash
scripts/backup/backup_providers.py       # Merge: superai_backup_manager + auto_firestore_backup + auto_cross_cloud_replicate
scripts/backup/backup_telegram.py        # Merge: telegram_backup_vault + telegram_code_backup + restore_from_telegram
```

### 3. SPLIT: tools/tool_knowledge_injector.py (2044 lines → 4 files)
```python
tools/knowledge/cards.py        # ToolKnowledgeCard class (~200 lines)
tools/knowledge/card_builder.py # build_knowledge_cards() function (~800 lines)
tools/knowledge/injector.py     # ToolKnowledgeInjector class (~300 lines)
tools/knowledge/cli.py          # main() function (~70 lines)
```

### 4. SPLIT: frontend/src/components/admin/CIDashboard.tsx (1297 lines → 8 files)
```typescript
admin/ci/Badge.tsx, ScoreCircle.tsx, ProgressBar.tsx, InsightCard.tsx, JobRow.tsx
admin/ci/CIDashboard.tsx    (main, ~850 lines)
admin/ci/types.ts           (all interfaces)
admin/ci/utils.ts           (helper functions)
```

### 5. REORGANIZE: admin/ folder (47 flat files → 6 subdirectories)
```
admin/
├── ci/         (8 files) - CI/CD components
├── data/       (4 files) - Data browsing
├── security/   (4 files) - Security dashboards
├── infra/      (5 files) - Infrastructure monitoring
├── auth/       (3 files) - Authentication
└── shared/     (5 files) - Reusable components
```

---

## 📊 NUMBERS AT A GLANCE

| Action | Files Affected | Impact |
|--------|---------------|--------|
| **MERGE** small files | ~80 files → ~25 | -55 files |
| **SPLIT** large files | ~17 files → ~60 | +43 organized files |
| **REORGANIZE** admin | 47 files | Better structure |
| **DELETE** duplicates/stubs | ~15 files | Cleanup |
| **NET RESULT** | | **~200 fewer files, better organization** |

---

## 🚨 CRITICAL DUPLICATES FOUND (Delete One)

1. `backend/services/auto_healer.py` = `backend/core/auto_healer.py` (864 lines each!)
2. `backend/evolution/temporal_system.py` = `backend/core/evolution/temporal_system.py` (905 lines each!)

**Action:** Choose canonical location (recommend `backend/services/`), delete the other.

---

## ✅ WEEKLY SCHEDULE

### Week 1: Merge Phase (Reduce file count by ~100)
- [ ] Day 1-2: Merge devops scripts
- [ ] Day 2-3: Merge backup scripts  
- [ ] Day 3-4: Merge resource_collection & testing scripts
- [ ] Day 5: Delete archives & stubs

### Week 2: Split Phase (Eliminate huge files)
- [ ] Day 1-2: Split tool_knowledge_injector.py
- [ ] Day 2-3: Split test_mcp_servers_integration.py
- [ ] Day 3-4: Split config_validator & dashboard components
- [ ] Day 5: Split remaining 1000+ line files

### Week 3: Organize Phase (Improve navigation)
- [ ] Day 1-2: Reorganize admin/ into subdirectories
- [ ] Day 2-3: Split monitoring & AI modules
- [ ] Day 3-4: Consolidate tests/
- [ ] Day 5: Update imports & verify all tests pass

---

*See full roadmap: supremeai_strict_roadmap.md for detailed instructions*
