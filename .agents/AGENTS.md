# SupremeAI Agent Core Directives

1. **Language Preference (ভাষাগত পছন্দ):**
   - ইউজারের ডিফল্ট ভাষা বাংলা। তাই সবসময় স্পষ্ট ও সাবলীল **বাংলায়** উত্তর দিতে হবে। (Banglish সম্পূর্ণ নিষিদ্ধ)।

2. **Error Resolution & Environment Verification (এরর ফিক্সিং রুল):**
   - যেকোনো এরর ফিক্স করার আগে বা নতুন কোনো কোড পুশ করার আগে **সবগুলো এনভায়রনমেন্ট (Local -> CI/CD -> Production) ধাপে ধাপে এবং ক্রমানুসারে (Sequentially & Time-wise) চেক করা বাধ্যতামূলক।** (Upstream Verification)
   - কোনো এরর সলভ করার পর অবশ্যই `docs/LESSONS_LEARNED.md` ফাইলটি নতুন লার্নিং দিয়ে আপডেট করতে হবে।

3. **Development Guidelines (ডেভেলপমেন্ট গাইডলাইন):**
   - প্রোজেক্ট ডেভেলপমেন্টের সময় সবসময় রুট ফোল্ডারে থাকা প্রোজেক্টের মেইন রুলস ফাইল `.blackboxrules` কঠোরভাবে অনুসরণ করতে হবে। (Location: `./.blackboxrules`)

4. **Proactive Automation (অটোমেশন):**
   - ইউজারকে অহেতুক প্রশ্ন না করে, যেই কাজগুলো নিজে থেকে স্বয়ংক্রিয়ভাবে (automatically) করে ফেলা সম্ভব, তা সাথে সাথে করে ফেলতে হবে।
