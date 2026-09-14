# M0-G — QA Spec Completion (M0.7) — Decision Table & Evidence

- Date: 2026-09-14
- Branch: `m0-g/qa-spec-completion`
- Roadmap item: `docs/plans/UNIFIED_NEXT_ROADMAP_2026-09-15.md` **M0.7** — "QA spec completion: write `qa/playwright/*/.auth/setup.ts` skeletons, convert 15 `test.fixme` → real specs (5 customer / 5 admin / 5 security)"
- Closes: audit §5.4 (`docs/audits/FULL_SYSTEM_AUDIT_2026-09-14.md`)
- Policy followed: honest conversion, not fake-green — a `test.fixme` became a real `test` **only** when every remaining prerequisite is (a) implemented here, or (b) a runtime environment variable / deployed QA_BASE_URL, i.e. the same prerequisites every authenticated E2E test has.

## 0. Ground-truth correction

The roadmap (inherited from the Task 9 reality-check) states **15** `test.fixme` blocks (5/5/5). The actual count on `main` @ `9757ad1` is **13**:

| File | fixme blocks | qa-ids |
|---|---|---|
| `qa/playwright/customer/customer.spec.ts` | 4 | C-01, C-05, C-08, C-10 |
| `qa/playwright/admin/admin.spec.ts` | 4 | A-02, A-05, A-06, A-07 |
| `qa/playwright/security/isolation.spec.ts` | 5 | S-02, S-03, S-06, S-08, S-09 |
| **Total** | **13** | |

Converted: **7** · Kept as fixme: **6** (all six are gated on missing features / fixture / ops work that cannot be conjured by adding `data-testid` attributes — reasons per row below).

## 1. Pre-existing bug found and fixed: the auth setups never ran

The two `.auth/setup.ts` skeletons from Task 7-e were **dead code** — `playwright test --list --project=setup-customer` collected **0 tests** since they were written:

1. **Filename vs `testMatch` mismatch (primary):** the projects match `/customer\/\.auth\/.*\.setup\.ts/` — the canonical Playwright pattern requires a `.` **before** `setup` (`<name>.setup.ts`). A file named plain `setup.ts` never matches, so the setup projects silently had zero tests.
2. **Comment-terminating glob (latent):** the skeleton JSDoc contained a literal `**/workspace` (from `waitForURL('**/workspace')`). Inside a `/** … */` comment the sequence `**/` terminates the block, turning the rest of the docstring into code — a syntax error once the file finally got collected.

Fix: renamed both to the canonical `auth.setup.ts` (layout `qa/playwright/<role>/.auth/auth.setup.ts` preserved per the roadmap), rewrote the header comments (the glob is spelled as a string concatenation in prose), and implemented the real automation (§3). Verified: `--list --project=setup-customer --project=setup-admin` now collects both.

## 2. Part-9 `data-testid` instrumentation (frontend)

Attribute-only additions; no refactor. Typecheck `tsc -p tsconfig.app.json --noEmit`: **0 errors**.

| File | Testids added |
|---|---|
| `frontend/src/pages/auth/LoginPage.tsx` | `email-input`, `password-input`, `login-submit` |
| `frontend/src/components/admin/auth/AdminLogin.tsx` | `admin-email-input`, `admin-password-input`, `otp-input`, submit button `otp-submit`/`admin-login-submit` (stage-aware: the same form button serves both gate stages) |
| `frontend/src/components/admin/auth/AdminAuthenticated.tsx` | `admin-shell` (stepped-up console root) |
| `frontend/src/components/admin/Dashboard.tsx` | `admin-kpi` ×4 (overview KPI cards) |
| `frontend/src/components/shell/RoleAwareNavRail.tsx` | `{context}-{actionId}-tab` on every nav action button (e.g. `admin-overview-tab`, `admin-tenants-rbac-tab`) |
| `frontend/src/components/admin/auth/UserManager.tsx` | `user-list` (registry list container) |
| `frontend/src/components/shell/GlobalHeader.tsx` | `account-menu-btn`, `logout-btn` (profile dropdown) |

Notes:
- Already on `main`: `SecretsPage.tsx` carried `new-key-name` / `create-key-btn` — S-08's "key-creation data-testid" blocker was already satisfied.
- **Not** instrumented: `create-project-btn/project-name-input/create-project-submit` and `upload-btn/file-input/upload-submit` — the /projects and /files surfaces (`WorkspaceModulePage`) are static module pages with **no** create-project or upload UI. A `data-testid` cannot be attached to DOM that does not exist; building those features is out of M0.7 scope (see C-05/C-08 rows).
- Register form: no fixme blocker references register testids (verified across all 13 titles) — not touched, per "only what the blockers name".

## 3. Auth setup implementation

- `qa/playwright/customer/.auth/auth.setup.ts`: credential guard kept verbatim → `goto /login` → fill the three Part-9 testids → `waitForURL('**/workspace')` (plus a `toHaveURL` assert) → `storageState({ path: 'qa/results/.auth/customer.json' })` (parent dir pre-created).
- `qa/playwright/admin/.auth/auth.setup.ts`: credential guard kept (fails closed without `QA_ADMIN_EMAIL/PASSWORD` and `QA_ADMIN_OTP` or `QA_ADMIN_TOTP_SECRET`) → stage 1 main login as above → `goto /admin` → AdminGate credentials (`admin-email-input`/`admin-password-input`/`admin-login-submit`) → OTP challenge (`otp-input`/`otp-submit`), where the OTP is `QA_ADMIN_OTP` or an RFC-6238 TOTP (SHA-1, 30 s, 6 digits) derived locally from `QA_ADMIN_TOTP_SECRET` via `node:crypto` — the secret never leaves the machine → race-waits the `trusted_browser` fast path vs. the challenge → waits for `admin-shell` visible → `storageState({ path: 'qa/results/.auth/admin.json' })`.

Runtime prerequisites (environment, unchanged by this work): dedicated QA accounts as env vars (never production), and a `QA_BASE_URL` deployment whose backend authenticates them.

## 4. Per-test decision table (13 rows)

| qa-id | Was-fixme blocker (title) | Decision | Reason | Env prerequisites after conversion |
|---|---|---|---|---|
| C-01 | needs data-testid (email-input/password-input/login-submit) + QA customer credentials | **converted** | All three testids implemented on `LoginPage`; login flow automated in customer `auth.setup.ts` | `QA_CUSTOMER_EMAIL/PASSWORD`; QA_BASE_URL deployment with reachable auth backend |
| C-05 | needs data-testid (upload-btn/file-input) + reachable storage backend | **kept fixme** | /files is a static module page — there is no upload UI to attach `upload-btn`/`file-input`/`upload-submit` to; needs the file-upload feature first, and the checklist demands backend-storage evidence (visible after reload) | n/a (needs feature work) |
| C-08 | needs data-testid (create-project-btn/project-name-input/create-project-submit) | **kept fixme** | /projects is a static module page — no create-project control flow exists; instrumentation impossible without the feature | n/a (needs feature work) |
| C-10 | logout control in GlobalHeader lacks a stable selector | **converted** | `account-menu-btn` + `logout-btn` added to `GlobalHeader`; body now opens the dropdown before clicking logout (menu is closed by default — the draft body would have timed out) | customer storage state from setup-customer |
| A-02 | needs QA_ADMIN_* secrets + otp-input/otp-submit data-testid (Part 9) | **converted** | Gate testids implemented; body corrected to drive the REAL two-stage flow (main login → AdminGate credentials → OTP challenge) instead of the drafted single-hop version, which never matched the app | `QA_ADMIN_EMAIL/PASSWORD`; live backend answering `otp_required` for the dedicated QA admin |
| A-05 | customer JWT transport (Bearer header vs cookie) not yet verified | **kept fixme** | Blocker is fixture/verification work (extract a customer JWT from storage state; prove the transport), not selectors — converting now would fake-green an unverified 403 contract | n/a (needs Part-9 fixture pass) |
| A-06 | AdminConsole internals lack data-testid (admin-shell/admin-kpi); needs admin storage state | **converted** | `admin-shell` on the console root, `admin-kpi` on the overview KPI cards; storage state produced by setup-admin | admin storage state (⇒ `QA_ADMIN_*` + live backend) |
| A-07 | sub-tab controls lack data-testid; needs admin storage state | **converted** | Nav action buttons carry `admin-<actionId>-tab`; the "users" panel is the registry's Tenants/RBAC sub-tab (`tenants-rbac` → `UserManager`), so the selector is `admin-tenants-rbac-tab` — grounded in `navigationRegistry.ts` (the draft's `admin-users-tab` id has no counterpart in the real nav); `user-list` added to the registry list | admin storage state (⇒ `QA_ADMIN_*` + live backend) |
| S-02 | needs QA_USER_A/QA_USER_B accounts + stable project-id URL scheme | **kept fixme** | Needs two dedicated QA account fixtures AND a `/projects/:id` route (route graph has none — catch-all 404 page returns 200, so the 403/404 status assertion cannot pass honestly yet) | n/a (needs fixtures + route scheme) |
| S-03 | needs QA_ADMIN_* secrets + otp-input data-testid (Part 9) | **converted** | `otp-input` implemented; body builds the "authenticated-but-not-stepped-up" context live (security project has no storage state) and asserts the AdminGate → OTP challenge with no console data leak (`/api/v1/admin/stats` 401/403) | `QA_ADMIN_EMAIL/PASSWORD`; live backend answering `otp_required` |
| S-06 | needs share-creation fixtures for two users | **kept fixme** | Needs share fixtures (valid share id for user A + marker content from user B); selectors exist (`/share/:shareId` is routed), fixtures do not | n/a (needs share fixtures) |
| S-08 | needs key-creation data-testid + scratch QA account | **converted** | `new-key-name`/`create-key-btn` already on `main`; body corrected to actually create a key (fill the name — the button is disabled otherwise, the draft click-on-disabled would have timed out), then assert the one-time banner plaintext does not survive reload; the checklist's literal `sk-live` assertion kept alongside (real prefix is `sk-supreme-…`, masked `sk-supreme-xxxx****yyyy`) | customer storage state (scratch QA account); live `/api/api-keys` backend; writes only to the dedicated QA account |
| S-09 | DEFERRED: capture staging header baseline before enabling hard assertions | **kept fixme** | Blocker is OPS EVIDENCE (first staging header capture, 08-production-preflight), not code — enabling hard assertions now would assert whatever headers happen to exist | n/a (needs staging evidence capture) |

## 5. Contract sync (qa/checklist/*.yaml)

For the 7 converted items the `manual_note`s were updated (Resolved (M0-G) + prerequisites); for the 6 kept items they now state the precise remaining blocker. Actions corrected where the spec body was corrected: C-10 (two-click logout), A-02 (AdminGate steps), A-07 (`admin-tenants-rbac-tab`), S-03 (gate fill steps), S-08 (name fill). `bun qa/scripts/validate-checklist.ts`: schema valid, 40 items, ids unique. `bun qa/scripts/route-audit.ts`: 40/40 routes verified.

## 6. Evidence

| Check | Result |
|---|---|
| `bunx playwright test -c qa/playwright.config.qa.ts --list` | **38 tests in 6 files** collected (guest 10, customer 10, admin 7, security 9 + setup-customer, setup-admin). Guest/Customer/Admin/Security all compile; no collection errors |
| `--list --project=setup-customer --project=setup-admin` | **2 setup tests collected** (0 before the M0-G filename fix) |
| fixme count | 13 → **6** (`bun qa/scripts/coverage-matrix.ts`: Real 30, Fixme 6, Uncovered 0, AutoCoverage 100%) |
| `cd frontend && bun run typecheck` (`tsc -p tsconfig.app.json --noEmit`) | **exit 0, no errors** |
| `bun qa/scripts/validate-checklist.ts` | ✅ 40 items schema-valid, ids unique (36 automated / 4 manual) |
| `bun qa/scripts/route-audit.ts` | ✅ 40/40 routes exist |
| `bun qa/scripts/coverage-matrix.ts` | ✅ advisory; Real 30 / Fixme 6 / Uncovered 0 |
| `bun qa/scripts/generate-report.ts --self-test` | ✅ all 4 fixtures PASS (offline) |
| TOTP derivation (`node:crypto` helper in admin `auth.setup.ts`) | ✅ matches all four RFC 6238 SHA-1 test vectors (t=59 → 287082, t=1111111109 → 081804, t=1234567890 → 005924, t=2000000000 → 279037) |
| Full playwright RUN | **not executed in this sandbox** — requires a live `QA_BASE_URL` deployment (vite preview + reachable backend) and QA account secrets; running unconverted pieces locally would produce red, not evidence. The `--list` + validators above are the static proof |

## 7. Deviations from the roadmap item text

1. **15 → 13 fixme:** the roadmap's 5/5/5 count was a miscount (actual 4/4/5). Documented above rather than invented.
2. **6 fixme intentionally remain:** the roadmap's exit criterion says "E2E fixme count 15 → 0"; reaching literal zero would have required shipping the file-upload/create-project features or asserting unverified behavior (A-05, S-09) — exactly the fake-green this milestone forbids. The honest completion is 7 converted + 6 precisely-diagnosed.
3. **Setup file renamed** `.auth/setup.ts` → `.auth/auth.setup.ts` (path per roadmap preserved; filename made canonical) — required because the original files never matched their own `testMatch` and thus never ran.
4. **Test bodies corrected where the drafted ones did not match the real DOM** (C-10 dropdown, A-02/S-03 two-stage gate, A-07 registry-grounded selector, S-08 name-fill + real masking assertion). Each is documented in the spec comments and the table above.
