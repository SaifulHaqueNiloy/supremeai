# ⚖️ Rule: 70/30 Pull Request & Change Evaluation Framework

> **Weighting:** 70% System & Business Benefit · 30% Technical Hygiene & Mergeability  
> **Constitutional Anchor:** AGENTS.md Rule 0 ("Every PR must make the system measurably better — not just different.")

---

## 1. The Core Law
Never evaluate a Pull Request solely or primarily by whether it is "mergeable" or "green". Mergeability and passing CI are merely prerequisites (30%). The decisive factor (70%) is whether the change brings tangible, high-ROI benefit to SupremeAI.

---

## 2. Evaluation Scorecard

### 💎 The 70%: System & Business Benefit (Decisive)
1. **Real Problem Solved**: Fixes a reproducible bug, closes a security hole, or fulfills an active core requirement.
2. **Measurable Improvement**: Makes code faster, leaner, more reliable, or more secure.
3. **Low Maintenance Debt**: Does not add unnecessary complexity, dead code, or unmaintained dependencies.
4. **Risk vs. Reward**: The risk of regression is heavily outweighed by the operational benefit.

*If a PR scores poorly on the 70%, it MUST NOT be merged, even if it is 100% mergeable and green.*

### 🛠️ The 30%: Technical Hygiene & Mergeability (Prerequisite)
1. Git mergeable (zero conflicts with main).
2. All CI gates green or validly diagnosed.
3. Meets atomic invariant (1 issue = 1 PR).
4. Full type-checking and automated test verification.
