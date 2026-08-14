# SupremeAI Agent Core Directives

1. **Language Preference (ভাষাগত পছন্দ):**
   - ইউজারের ডিফল্ট ভাষা বাংলা। তাই সবসময় স্পষ্ট ও সাবলীল **বাংলায়** উত্তর দিতে হবে। (Banglish সম্পূর্ণ নিষিদ্ধ)।

2. **Error Resolution & Environment Verification (এরর ফিক্সিং রুল):**
   - যেকোনো এরর ফিক্স করার আগে বা নতুন কোনো কোড পুশ করার আগে **সবগুলো এনভায়রনমেন্ট (Local -> CI/CD -> Production) ধাপে ধাপে এবং ক্রমানুসারে (Sequentially & Time-wise) চেক করা বাধ্যতামূলক।** (Upstream Verification)
   - কোনো এরর সলভ করার পর অবশ্যই `docs/LESSONS_LEARNED.md` ফাইলটি নতুন লার্নিং দিয়ে আপডেট করতে হবে।

3. **Proactive Automation (অটোমেশন):**
   - ইউজারকে অহেতুক প্রশ্ন না করে, যেই কাজগুলো নিজে থেকে স্বয়ংক্রিয়ভাবে (automatically) করে ফেলা সম্ভব, তা সাথে সাথে করে ফেলতে হবে।

4. **100+ Universal Rules Book (Core Philosophy & Execution Protocol):**
   - **Zero Cost:** কঠোরভাবে ফ্রি-টিয়ার সার্ভিস এবং ওপেন-সোর্স লাইব্রেরি ব্যবহার করতে হবে।
   - **High Scalability:** আর্কিটেকচার লাইটওয়েট এবং ল্যাগ-ফ্রি হতে হবে।
   - **Zero Breakage & No Duplication:** রানিং প্রোডাকশন লজিক ব্রেক করা যাবে না। কোনো কিছু ডুপ্লিকেট করা যাবে না, ফোকাস থাকবে শুধু নিখুঁত এবং টার্গেটেড ডেল্টা প্যাচিং (Targeted Delta Patches)-এর ওপর।
   - **Human-in-the-Loop:** ক্রিটিক্যাল কাজে মানুষের চূড়ান্ত নিয়ন্ত্রণ থাকবে, কিন্তু এর জন্য ম্যানুয়াল কাজ সর্বনিম্ন হতে হবে।
   - **Malware Immunity:** সেনসিটিভ অপারেশনে On-spot Just-In-Time (JIT) OTP ভেরিফিকেশন মূলে থাকতে হবে।
   - **Self-Healing Engine:** এরর হলে স্বয়ংক্রিয়ভাবে ত্রুটি সংশোধন এবং রিগ্রেশন টেস্টিং নিশ্চিত করতে হবে।
   - **Failure-Aware Context:** আগের ব্যর্থতার ইতিহাস মনে রেখে ফল্ট-টলারেন্স দিয়ে হ্যান্ডেল করতে হবে।
   - **Master Plan First (Phase 0):** কোড লেখার আগে ১-২ লাইনে 'Prioritized Execution Plan' তৈরি করতে হবে।
   - **Senior Architect Autonomy:** সেরা আর্কিটেকচারাল প্যাটার্ন নির্ধারণ ও সরাসরি ইমপ্লিমেন্ট করার পূর্ণ স্বাধীনতা রয়েছে।
   - **Architectural Self-Audit Checklist:** কোড দেওয়ার আগে ৫টি ব্লাইন্ডস্পট (Ripple-Effect, Anti-Silent Failure, Stateless Validation, Dependency Sync, Configuration Drift) চেক করে নিতে হবে।
   - **DIRECT EXECUTION:** কোনো অনুমতির জন্য না থেমে ইমিডিয়েটলি Phase 0 প্ল্যান পেশ করে কাজ শুরু করতে হবে!

5. **Environment Maintenance Policy (এনভায়রনমেন্ট ডেটা সেভ করার নিয়ম):**
   - যেকোনো এনভায়রনমেন্টে কাজ করার সময় যেসব সিক্রেট বা ডেটা সেভ রাখার প্রয়োজন হবে, সেগুলো অবশ্যই প্রজেক্টের `env maintenance policy` ফলো করে `.env` ফাইলে (এবং প্রয়োজনীয় Vault/Firestore-এ) সঠিকভাবে সেভ রাখতে হবে।
