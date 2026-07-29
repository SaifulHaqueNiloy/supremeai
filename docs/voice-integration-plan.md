# 🎙️ SupremeAI 2.0 — Hybrid Voice (TTS & STT) Integration Plan
_Status: PLANNING / APPROVED STRATEGY_
_Author: Principal Autonomous AI Architect_

---

## 📌 Approach (হাইব্রিড আর্কিটেকচার)
আমাদের প্রজেক্টের **Zero-Cost** এবং **High Scalability** নীতি বজায় রেখে নিম্নোক্ত হাইব্রিড ভয়েস সিস্টেমটি ইমপ্লিমেন্ট করা হবে:

1. **ডিফল্ট অপশন (১০০% ফ্রি ও আনলিমিটেড):**
   - **Text-to-Speech (TTS):**
     - **Web & VS Code Ext:** ব্রাউজারের নেটিভ `Web Speech API (window.speechSynthesis)`.
     - **Backend:** Google Cloud TTS (Standard Voice) যা প্রতি মাসে ৪ মিলিয়ন (40 Lakh) ক্যারেক্টার সম্পূর্ণ ফ্রিতে অফার করে।
   - **Speech-to-Text (STT):**
     - **Web/VS Code/Mobile:** নেটিভ ওএস/ব্রাউজার রিকগনিশন (webkitSpeechRecognition) যা চমৎকার বাংলা ও ইংরেজি রিকগনাইজ করে।

2. **প্রিমিয়াম অপশন (ইউজার-কনফিগারড এপিআই কি):**
   - **ভয়েস ক্লোনিং ও ইমোশন ভয়েস:** ElevenLabs ইন্টিগ্রেশন। ব্যবহারকারী তার সেটিংসে নিজের **ElevenLabs API Key** যোগ করলে এটি সক্রিয় হবে (ফ্রি অ্যাকাউন্টে ১০,০০০ ক্যারেক্টার/মাস ও ওয়ান-ক্লিক ক্লোনিং সুবিধা থাকবে)।
   - **হাই-কোয়ালিটি ট্রান্সক্রিপশন:** OpenAI Whisper API (ব্যবহারকারীর এপিআই কি দিয়ে)।

---

## 🎯 Scope (পরিধি)

### In Scope:
- **Web Client & VS Code Webview:** চ্যাট প্যানেলে মাইক্রোফোন বাটন (STT) এবং চ্যাট মেসেজের পাশে স্পিকার বাটন (TTS) ইন্টিগ্রেশন।
- **Backend API Gateway (`backend/api/routes/voice.py`):** Google Cloud TTS এবং ElevenLabs ক্লায়েন্ট রাউটার।
- **Flutter Mobile (`apps/mobile`):** `flutter_tts` এবং `speech_to_text` প্যাকেজ ইন্টিগ্রেশন।

### Out Scope:
- ব্যাকএন্ডে লোকাললি বিশাল সাইজের হুইস্পার বা কোকুই টিটিএস মডেল হোস্ট করা (যা গিটহাব রানার ও লাইভ মেমরি হ্যাক করতে পারে)।

---

## 🚀 Action Items (ধাপসমূহ)

### Phase 1: Backend Gateway (`backend/`)
- [ ] **Create voice router:** `backend/api/routes/voice.py` তৈরি করা।
  - Google Cloud TTS ক্লায়েন্ট সেটআপ (Standard & WaveNet voice API)।
  - ElevenLabs API ক্লায়েন্ট সেটআপ (ভয়েস ক্লোন ক্লোনিং এপিআই ও কাস্টম ভয়েস জেনারেশন)।
- [ ] **Register router:** `backend/api/routers.py` এবং `validate_router_imports.py`-তে রাউটটি যোগ করা।

### Phase 2: Web & VS Code Layer
- [ ] **Web Speech API Interface:** `apps/studio-client/` এ স্পিকার এবং মাইক্রোফোন আইকন ইমপ্লিমেন্ট করা।
- [ ] **User Credentials Store:** সেটিংস প্যানেলে `ElevenLabs API Key` এবং `ElevenLabs Voice ID` ইনপুট ফিল্ড ও লোকালস্টোরেজ সেভিং মেকানিজম যুক্ত করা।

### Phase 3: Flutter Mobile Layer
- [ ] **Add dependencies:** `pubspec.yaml`-এ `flutter_tts` এবং `speech_to_text` কনফিগার করা।
- [ ] **Native permissions configuration:** Android এবং iOS এর জন্য অডিও রেকর্ডিং ও ট্রান্সক্রিপশন পারমিশন ফাইল আপডেট করা।

---

## 🔬 Validation Plan (যাচাইকরণ)
- **Local Smoke Test:** `validate_router_imports.py` রান করে ভয়েস রাউট সাকসেস চেক করা।
- **Security Check:** `Ruff` এবং `CodeQL` স্ক্যানের মাধ্যমে কোনো হার্ডকোডেড ভয়েস কি বা ক্রেডেনশিয়াল পাস হচ্ছে না তা নিশ্চিত করা।
