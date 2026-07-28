# Pre‑Merge Gate (CI) vs Pre‑Commit Hook (Local) – পার্থক্য বিশ্লেষণ  
**প্রোজেক্ট:** SupremeAI 2.0  
**তারিখ:** 2026‑07‑28  

---  

## ১. Pre‑Merge Gate (GitHub Actions) – `supreme-core-ci.yml`  

### Job: `pre-merge-gate`  

| ধাপ (Step) | Pre‑Commit‑এ উপস্থিত? | সংক্ষিপ্ত বিবরণ |
|------------|----------------------|----------------|
| **Set Trivial Change Output** | ❌ | ডক‑এন্ড/মার্কডাউন‑মাত্র পরিবর্তন সনাক্ত করে, ত্রিভিয়াল হলে পরবর্তী jobs বন্ধ করে। |
| **Set up Python** | ❌ (Pre‑Commit সিস্টেম Python ব্যবহার করে) | `actions/setup-python@v5` – Python 3.11 সেট‑আপ। |
| **Install gate & backend dependencies** | ❌ | `poetry install --only main --no-root` – ব্যাকএন্ড‑এর ডিপেন্ডেন্সি ইন্সটল। |
| **Gate 1 – Zero‑Gap Stub/Placeholder Data Check** | ✅ (`stub-data-check` hook) | `scripts/find_stub_data.py --path . --fail-on HIGH` – স্টাব/প্লেসহোল্ডার ডেটা ব্লক। |
| **Gate 1.5 – Security Blind Spot Scan** | ✅ (`supremeai-blindspot-scan` hook) | `scripts/security/auto_find_blindspots.py` – হার্ডকোডেড সিক্রেট, SQL‑Injection ইত্যাদি স্ক্যান। |
| **Gate 2 – Ruff Linting (No Silent Bugs)** | ⚠️ (আংশিক) | Pre‑Commit‑এ `ruff` চেক (no‑fix) চালায়। CI‑এ **প্রথমে `--fix`** চালানো, তারপর `--no‑fix` দিয়ে যাচাই → **auto‑fix + verify** দৌটি‑Phase। |
| **Bot Commit Detection** | ❌ | CI‑Bot ক밋 discover করে `strict` রাউটার ইম্পোর্ট টেস্ট চালায়। |
| **Gate 0 – Router Import Smoke‑Test** | ✅ (`router-smoke-test` hook) | `poetry -C backend run python ../scripts/ci/validate_router_imports.py` – প্রতিটি রাউটার আম্পোর্ট চেক। |
| **Gate 3.5 – Admin Router Auth Lint Guard** | ❌ | অ্যাডমিন‑প্রিফিক্স রাউটারে `Depends(get_current_admin)` নিশ্চিতকরণ স্ক্রিপ্ট (`.github/scripts/verify_admin_auth.py`)。 |
| **Gate 3 – Observability Check (No httpx without timeout)** | ❌ | `httpx.AsyncClient()`‑এ explicit timeout না থাকলে ব্যর্থ হয়। |

### সারসংক্ষেপ (CI‑এ **কেবলমাত্র** Existing)
- **Trivial‑Change Detection** – ডক‑এন্ড/মার্কডাউন‑মাত্র শুধুমাশি কমিট detection。  
- **Python সেট‑আপ ও ডিপেন্ডেন্সি ইন্সটল** (Poetry)。  
- **Bot‑কমмит Detective** – CI‑বট ক밋েStrict রাউটার টেস্ট।  
- **অ্যাডমিন রাউটার Auth‑ল린্ট গার্ড** (`verify_admin_auth.py`)。  
- **HTTPX‑টাইমআউট অডিট** – `httpx.AsyncClient()`‑এ timeout নিশ্চিত করা।  
- **রাফ লিন্টিং** – `ruff check --fix` followed by `ruff check --no‑fix` (auto‑fix + verify) – Pre‑Commit‑এ শুঁধু `ruff check` (no‑fix) চলে।  

---  

## ২. Pre‑Commit Hook (Local) – `.pre-commit-config.yaml` (এবং `config/.pre-commit-config.yaml` – উভয়ই یکই)  

| Hook (Local) | CI‑এ সমতুল্য? | গল্প |
|--------------|--------------|------|
| **check‑yaml** | ❌ | YAML সিনট্যাক্স বৈধতা (`--allow-multiple-documents`) |
| **check‑json** | ❌ | JSON সংবرلক – ভাঙা JSON ব্লক |
| **check‑toml** | ❌ | TOML সিনট্যাক্স Validator (`pyproject.toml`‑এ)। |
| **check‑merge‑conflict** | ❌ | `<<<<<<<`、`>>>>>>>` মার্কার découvertes 시 커밋 차단 |
| **debug‑statements** | ❌ | `pdb.set_trace()`, `breakpoint()` discovery → 커밋 차단 |
| **end‑of‑file‑fixer** | ❌ | EOF 끝에 개행 강제 |
| **trailing‑whitespace** | ❌ | 줄 끝 공백 제거 (마크다운 예외) |
| **detect‑private‑key** | ❌ | SSH/SSL 개인 키 커밋 차단 (특정 테스트 제외) |
| **check‑ast** | ❌ | Python 구문 검사 (AST) |
| **secret‑hunter** | ❌ | `scripts/devops/secret_scan_ci.py --staged` – 스테이지된 파일에서 비밀/토큰 스캔 |
| **ruff** | ✅ (Gate 2와 부분 일치) | `ruff check backend --config=backend/pyproject.toml --extend-ignore=S101,S110,S603,S607,S104,S105,S107,S108,S306,S310,S311,S314,S608,E501,E402` (수정 없음) |
| **ruff‑format** | ❌ | `ruff format backend --config=backend/pyproject.toml` – 코드 포맷 자동 적용 |
| **mypy** | ❌ | 정적 타입 검사 (`--ignore-missing-imports --no-strict-optional`) – 특정 디렉터리 제외 |
| **eslint‑frontend** | ❌ | `pnpm -C apps/studio-client exec eslint --max-warnings=9999 src/ --ext .ts,.tsx` – TS/TSX 임포트·타입 검사 |
| **supremeai‑blindspot‑scan** | ✅ (Gate 1.5와 동일) | `scripts/security/auto_find_blindspots.py` – 하드코딩된 비밀·SQL 삽입 등 검사 |
| **stub‑data‑check** | ✅ (Gate 1과 동일) | `scripts/find_stub_data.py --path . --fail-on HIGH` – 스텁/플레이스홀더 데이터 차단 |
| **router‑smoke‑test** | ✅ (Gate 0과 동일) | `poetry -C backend run python ../scripts/ci/validate_router_imports.py` – 라우터 임포트 테스트 |
| **free‑tier‑size‑guard** | ❌ | `scripts/ci/check_free_tier_limits.py` – Render/GitHub/Vercel/Firebase 무료 티어 사용량 체크 (80% 경고, 95% 커밋 차단) |

---  

## ৩. পার্থক্য সারসংক্ষেপ  

### ✅ CI‑এ **কিন্তু** Pre‑Commit‑এ **অনুপস্থিত**  
1. **Trivial‑Change Detection** – দক‑এন্ড/মার্কডাউন‑মাত্র শুধুমাশি কিমিট বロック।  
2. **Python সেট‑আপ & ডিপেন্ডেন্সি ইন্সটল** – CI‑এ বিল্ড এনভায়রনমেন্ট 준비。  
3. **Bot‑কমмит Detective** – CI‑봇 커밋 시 라우터 임포트를 **strict** 모드로 실행.  
4. **অ্যাডমিন রাউটার Auth‑লিন্ট গার্ড** – `Depends(get_current_admin)` enforced on admin‑prefixed routes.  
5. **HTTPX‑টাইমআউট অডিট** – `httpx.AsyncClient()`‑এ timeout‑nya guarantee。  
6. **রাফ লিন্টিং** – CI‑এ `--fix` 다음 `--no‑fix` (자동 수정 + 검증) 2단계, Pre‑Commit‑에는 검사만 실행 (수정 없음).  

### ✅ Pre‑Commit‑এ **কিন্তু** CI‑এ **অনুপস্থিত**  
1. **বেসিক ফাইল হেলথ চেক** – YAML/JSON/TOML синтакси스, 머지 충돌, 디버그 문장, EOF/끝 공백, 개인 키, AST 검사 등.  
2. **Secret Hunter** – 스테이지된 파일에서 비밀·토큰 스캔 (CI에는 별도 작업 없음).  
3. **Ruff Formatter** – 코드 스타일 자동 적용 (`ruff format`).  
4. **Mypy** – 정적 타입 검사 (특정 디렉터리 제외).  
5. **ESLint Frontend** – TS/TSX 임포트·타입 검사 (프론트엔드 전용).  
6. **Free‑Tier Size Guard** – 무료 티어 리소스 사용량 모니터링 및 초과 시 경고/차단.  

### 📌 olhar নোট  
- 두 파이프라인은 **중복되는 검사**도 많습니다:  
  - Stubデータチェック (`Gate 1` ↔ `stub-data-check`)  
  - 보안 블라인드 스팟 스캔 (`Gate 1.5` ↔ `supremeai-blindspot-scan`)  
  - 라우터 임포트 스모크 테스트 (`Gate 0` ↔ `router-smoke-test`)  
- 다만 **구성 및 실행 방식**에 차이가 있습니다:  
  - **Ruff** – CI에서는 자동 수정 후 검증, Pre‑Commit에서는 검사만 수행.  
  - **Bot‑Commit Detection** – CI 전용 로직으로, 로컬에서는 적용되지 않음.  
  - **프리‑티어 가드** – 로컬 개발 시 즉각적인 피드백을 제공하지만 CI에서는 별도 작업이 없음 (일반적으로 별도 워크플로우 또는 수동 점검).  

---  

## ৪. সুপারিশ (Recommendations)  

1. **중복 검사 제거** – 가능한 한 로컬 Pre‑Commit과 CI에서 동일한 검사를 공유하여 불일치를 줄입니다. (예: `ruff` 옵션을 CI와 동일하게 `--fix` → `--no‑fix` 로 통일).  
2. **프리‑티어 가드를 CI에 추가** – 무료 티어 한도 초과 시 사전에 차단하여 배포 실패를 방지합니다.  
3. **Bot‑Commit Detection을 로컬에서도 시뮬레이션** – `PRE_COMMIT=1` 플래그를 이용해 동일하게 strict 모드 테스트를 실행할 수 있는 스크립트를 제공하면 로컬에서도 CI와 동일한 검증을 경험할 수 있습니다.  
4. **Documentation** – 각 검사의 목적을 README나 CONTRIBUTING에 간단히 적어두면 새 contributors가 로컬과 CI의 차이를 이해하기 쉬워집니다.  

---  

*이 문서는 SupremeAI 2.0 프로젝트의 **Pre‑Merge Gate (CI)** 와 **Pre‑Commit Hook (Local)** 간의 차이점을 벵골어로 정리한 것입니다. 필요에 따라 내용은 지속적으로 갱신되어야 합니다.*
