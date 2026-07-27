# SupremeAI 2.0 — দ্বিতীয় পর্যায় রুট-কজ রিফ্যাক্টরিং রিপোর্ট

**স্ক্যান স্কোপ:** সমগ্র `backend/core/` (১০১ ফাইল)  
**নতুন সমস্যা শনাক্ত:** ৬টি ফাইল এখনো Architectural Law ভায়োলেশনে আক্রান্ত

---

## চ্যাপ্টার ১: রুট-কজ ডায়াগনোসিস

### ১.১ | `multi_layer_cache.py` — Module-Level Redis Initialization (Critical)
**গলদ:** লাইন ৪২ ও ৪৯-এ `redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))` module-level এ execute হচ্ছে।  
এর মানে হলো Python ফাইলটি `import` করা মাত্রই Redis connection তৈরির চেষ্টা করা হয়, যা:
- pytest isolation ভাঙে (import = side effect)
- Cold start-এ Network call করে  
- Fallback URL `redis://localhost:6379` হার্ডকোড করা — Anti-Hardcode Rule লঙ্ঘন

### ১.২ | `swarm_pubsub.py` — Hardcoded Redis URL (Critical)
**গলদ:** লাইন ১৫-এ `self.redis = redis.from_url("redis://localhost")` — URL সম্পূর্ণ হার্ডকোড।  
Module-level `swarm_streamer = SwarmPubSub()` instance তৈরি মানে import করলেই Redis connect হয়।

### ১.৩ | `task_queue.py` — Module-Level os.getenv with Hardcoded Default (High)
**গলদ:** লাইন ১৫-এ `redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")` module-level এ।  
`settings` থেকে না নিয়ে `os.getenv` ব্যবহার করা Single Source of Truth ভঙ্গ।

### ১.৪ | `security_vault.py` — Silent Decrypt Failure + print() (High)
**গলদ:** লাইন ৩০-৩২-এ `except Exception as e: print(f"Error...")  return ""` —  
- `logger` নয়, `print()` ব্যবহার (production এ নিষিদ্ধ)
- decrypt fail হলে `""` রিটার্ন করে ক্রিপ্টোগ্রাফিক ব্যর্থতা চাপা দেওয়া হচ্ছে
- `ErrorEventBus` এ এমিট নেই

### ১.৫ | `email_service.py` — Hardcoded API URL + Silent Exception (High)
**গলদ:**  
- লাইন ১১: `self.api_url = "https://api.resend.com/emails"` — হার্ডকোড
- লাইন ৪৩: `except Exception as e: logger.error(...)  return False` — raise নেই, ErrorBus নেই
- লাইন ৫৫: HTML template-এ `https://supremeai.dev/studio` হার্ডকোড

### ১.৬ | `cloud_sandbox_orchestrator.py` — Hardcoded Provider URLs (High)
**গলদ:** লাইন ৪৮-৫০-এ `"https://api.runpod.io/v2"` এবং `"https://api.modal.com"` হার্ডকোড।  
প্রোভাইডার URL পরিবর্তন হলে কোড এডিট ছাড়া deploy করা যাবে না।
