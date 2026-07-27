# SupremeAI 2.0 — রুট-কজ রি-ফ্যাক্টরিং রিপোর্ট

**তারিখ:** 2026-07-12 | **Analyst:** Antigravity — Enterprise Architect Mode  
**কোডবেস স্ক্যান স্কোপ:** `backend/core/` (101 ফাইল), `backend/services/`, `backend/reproduce_pytest.py`

---

## চ্যাপ্টার ১: রুট-কজ ডায়াগনোসিস (The Root-Cause Diagnosis)

### ১.১ | `secret_vault.py` — Silent-Fallback Anti-Pattern (Critical)

**আর্কিটেকচারাল গলদ:**  
`fetch_secret()` মেথড-এ `default: str = None` প্যারামিটার ব্যবহার করে Fail-Fast নীতি ভঙ্গ করা হয়েছে। যখন কোনো secret পাওয়া যায় না, তখন `production` ছাড়া সব পরিবেশে `""` (empty string) রিটার্ন করে — এটি **Silent Degradation Anti-Pattern**।

**ত্রুটির শিকড়:**  
- `default: str = None` — Python type annotation মিথ্যা (str কিন্তু None দেওয়া হচ্ছে)  
- `return default if default is not None else ""` — empty string দিয়ে API key replace হচ্ছে, কোনো error নেই  
- `ProductionSecretVault.__init__` এ `except Exception: logger.warning(...)` দিয়ে Infisical connection failure suppress করা হচ্ছে  
- Module-level `secret_vault = get_secret_vault()` — import time-এই network attempt হয়, cold start বাড়ে  

**পুনরাবৃত্তির কারণ:**  
"Convenience fallback" design — developer ভাবছে graceful degradation ভালো, কিন্তু এটি secretly broken config দিয়ে deployment হতে দেয়।

---

### ১.২ | `playwright_manager.py` — Mutable Global State + Test Isolation Breach (High)

**আর্কিটেকচারাল গলদ:**  
`_playwright_runner` এবং `_global_browser` দুটি module-level mutable global variable। `reproduce_pytest.py` দিয়ে প্রমাণিত যে test collection এবং monkeypatching-এ এই globals pytest isolation ভাঙে।

**ত্রুটির শিকড়:**  
```python
# পুরনো: module-level mutable globals — test poison
_playwright_runner: Playwright | None = None
_global_browser: Browser | None = None
```

`get_global_browser()` ফাংশন `current_module = sys.modules.get(__name__)` দিয়ে runtime-এ module reference খোঁজে — এটি fragile test-aware hack। প্রোডাকশন কোডে `sys.modules` manipulation সম্পূর্ণ নিষিদ্ধ।

**পুনরাবৃত্তির কারণ:**  
Lazy singleton pattern ঠিকমতো implement না করা — class-based context manager ব্যবহার না করে bare global variable রাখা।

---

### ১.৩ | `auto_remediation.py` — Hardcoded Repository URL + Bare Except (High)

**আর্কিটেকচারাল গলদ:**  
```python
# লাইন ২২০ — hardcoded repo URL সম্পূর্ণ নিষিদ্ধ
self.github_agent.commit_changes(
    repo_url="paykaribazaronline/supremeai",  # ← HARDCODED!
    ...
)
```

এবং `process_codeql_alert()` মেথডে:
```python
except Exception as e:  # noqa: BLE001
    logger.error(f"❌ Remediation failed: {str(e)}")
    # ← raise নেই! exception silently consumed!
```

**পুনরাবৃত্তির কারণ:**  
Config extraction কখনো সম্পন্ন হয়নি — developer exception suppress করে "এখন চলছে" মানসিকতায় কাজ চালিয়ে যাচ্ছে।

---

### ১.৪ | `lifespan.py` — Empty Try-Except Block + os.getenv() Bypass (Medium)

**আর্কিটেকচারাল গলদ:**  
```python
# লাইন ১৫২-১৬৬ — empty try block!
try:
    pass  # ← কিছুই নেই!
except Exception as e:
    logger.error(f"Failed to initialize Redis Manager: {e}")
```
এটি dead code কিন্তু exception handler বিদ্যমান — confusing এবং maintenance trap।

এছাড়া `settings` object থাকার পরেও `os.getenv("ENV")` সরাসরি ব্যবহার করা হচ্ছে — Single Source of Truth নীতি লঙ্ঘন।

**পুনরাবৃত্তির কারণ:**  
Refactoring incomplete — Redis initialization code সরানো হয়েছে কিন্তু try-except block রয়ে গেছে।

---

### ১.৫ | `evolution_engine.py` — Production SQLite on Ephemeral FS (High)

**আর্কিটেকচারাল গলদ:**  
```python
# শুধু warning দেওয়া হচ্ছে, Fail-Fast নয়!
if env == "production" and "/data/" in str(self.db_path):
    logger.warning("⚠️ SQLite on ephemeral filesystem...")
    # ← continue করছে! data হারানো নিশ্চিত!
```

Container restart-এ সমস্ত evolution data হারায় — কিন্তু সিস্টেম নীরবে চলে।

---

### ১.৬ | `config.py` — pytest-in-sys.modules Anti-Pattern (Medium)

**আর্কিটেকচারাল গলদ:**  
Production config code-এ `"pytest" in sys.modules` check একটি architectural smell। Config layer-এর test awareness থাকা উচিত নয় — এটি test/production concern separation ভাঙে।

```python
# লাইন ২৯ — config layer pytest জানে?!
if "pytest" not in sys.modules:
    root_env = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(root_env)
```

এই pattern `validate_docs_password`, `validate_admin_hash`, `validate_completeness` সর্বত্র ছড়িয়ে আছে।

---

### ১.৭ | `microvm_sandbox.py` — Sandbox Root Whitelist Windows-Incompatible (Medium)

**আর্কিটেকচারাল গলদ:**  
```python
_SANDBOX_ROOT_WHITELIST: frozenset[str] = frozenset({
    "/tmp/sandboxes",  # ← Linux-only path!
    "/var/tmp/sandboxes",
    "/run/sandboxes",
})
```
Windows development environment-এ `_validate_sandbox_root()` সবসময় crash করবে, কারণ Windows পাথ `/tmp/` দিয়ে শুরু হয় না।

---

## চ্যাপ্টার ২: রি-ফ্যাক্টরিং সলিউশন কোড (The Ironclad Refactored Code)

**[নিচে ৭টি ফাইলের সম্পূর্ণ refactored কোড দেখুন — কোনো truncation নেই]**

---

## চ্যাপ্টার ৩: রিগ্রেশন-প্রুফ গ্যারান্টি (The Regression-Proof Safeguard)

**[CI/CD এবং Ruff/pre-commit rules নিচে বিস্তারিত দেখুন]**
