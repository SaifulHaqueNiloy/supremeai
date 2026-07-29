# ব্যাকএন্ড টেস্ট রিলায়েবিলিটি গাইডলাইন

এই ডকুমেন্টের উদ্দেশ্য: CI-তে test failure-এর সবচেয়ে সাধারণ, বারবার ফিরে আসা কারণগুলো
লিপিবদ্ধ করা, যাতে নতুন কোড/টেস্ট লেখার সময় এগুলো এড়ানো যায়। প্রতিটা পয়েন্ট এই রিপোতে
**সত্যিই ঘটা** একটা bug থেকে নেওয়া।

## ১. কোনো auth/middleware মডিউল থেকে import করার আগে module-এ সেটা সত্যিই আছে কিনা যাচাই করুন

`tests/conftest.py`-তে `ALLOW_TEST_AUTH_BYPASS` env var-এর একটা স্পষ্ট, লিখিত contract
ছিল (`_is_public_path(path) or (is_test_environment() and allow_bypass)`), কিন্তু
`core/security/auth_middleware.py`-তে সেটা কখনো implement করা হয়নি — `is_test_environment`
import-ই করা ছিল না। ফলাফল: ৩টা টেস্ট ফাইল জুড়ে ডজনখানেক টেস্ট `AttributeError` বা
`assert 401 == 200` দিয়ে ফেইল করছিল, কারণ প্রতিটা প্রোটেক্টেড এন্ডপয়েন্ট রিয়েল JWT
ছাড়া 401 রিটার্ন করত, টেস্ট যেটা আশা করেনি।

**নিয়ম:** কোনো মিডলওয়্যার/ডিপেন্ডেন্সি ফাইল লেখার বা edit করার সময়, যদি
`ALLOW_TEST_AUTH_BYPASS` বা অনুরূপ কোনো contract `conftest.py`/comment-এ ডকুমেন্টেড
থাকে, সেটা আসলে কোডে বাস্তবায়িত হয়েছে কিনা `grep` করে যাচাই করুন। শুধু docstring/comment
লেখা যথেষ্ট না — বাস্তব `if` কন্ডিশনে সেটা থাকতে হবে।

## ২. `@patch("module.name", ...)` লেখার আগে সেই নামটা সত্যিই সেই মডিউলে import করা আছে কিনা চেক করুন

`unittest.mock.patch("core.security.auth_middleware.is_test_environment", ...)` তখনই
কাজ করে যখন `auth_middleware.py`-তে সত্যিই `from utils.environment import
is_test_environment` লাইনটা আছে। যদি টেস্ট অন্য কোনো ফাইলের প্যাটার্ন কপি করে (যেমন
`core.security.api_key_middleware.is_test_environment` থেকে), কিন্তু টার্গেট মডিউলে
আসলে import করা না থাকে, তাহলে টেস্টটা `AttributeError`-এ ক্র্যাশ করবে, functional
bug না — অর্থাৎ টেস্ট ফেইল মানেই সবসময় প্রোডাকশন কোডে bug না, কখনো টেস্টের ভুল ধারণাও
হতে পারে। উভয় দিক থেকেই যাচাই করা জরুরি।

## ৩. `unittest.mock.patch("module.settings")`-এর মতো wholesale mock ব্যবহার করলে প্রতিটা নতুন settings ফিল্ড আপডেট করুন

`test_security_middleware.py` পুরো `settings` অবজেক্টকে `MagicMock()` দিয়ে replace
করত এবং শুধু ২টা attribute (`supremeai_api_token`, `supremeai_public_paths`) সেট করত।
`settings`-এ নতুন যোগ হওয়া যেকোনো boolean flag (যেমন `allow_test_auth_bypass`)
`MagicMock`-এ auto-truthy হয়ে যায় — explicitly `False` সেট না করলে সেটা সবসময়
"True" ধরে নেওয়া হয়, যেটা silent security-test bypass তৈরি করতে পারে।

**নিয়ম:** যখনই `settings`-এ নতুন কোনো boolean/security flag যোগ করবেন, রিপোতে
`patch("....settings")` করা প্রতিটা টেস্ট গ্রেপ করে দেখুন সেগুলোর নতুন flag-টার
জন্য explicit মান দরকার কিনা — বিশেষ করে "reject" আচরণ যাচাই করা টেস্টগুলোতে।

## ৪. একটা root-cause fix করার পর পুরো test suite আবার চালান, শুধু যেটা ফিক্স করলেন সেটা না

একটা মিডলওয়্যার fix দিয়ে ~১৫টা failing test ঠিক হয়েছিল, কিন্তু একই fix ৪টা **নতুন**
regression তৈরি করেছিল (এমন টেস্ট যেগুলো ইচ্ছাকৃতভাবে "reject" behavior যাচাই করত,
নতুন bypass logic-এর কারণে ভুলভাবে পাস করে যাচ্ছিল)। যদি শুধু targeted টেস্টগুলো
আবার চালানো হতো, এই regression ধরা পড়ত না।

**নিয়ম:** যেকোনো shared middleware/dependency ফাইল বদলানোর পর পুরো
`pytest -n auto --dist=loadfile` স্যুট চালিয়ে দেখুন নতুন কোনো ফেইলিউর যোগ হলো কিনা,
শুধু আগের ফেইলিউরগুলো ঠিক হলো কিনা তা না।

## ৫. sandbox/local এনভায়রনমেন্টে না-চালানো test path-কে "কাজ করছে" ধরে নেবেন না

আগের বেশ কয়েকটা audit পাস torch/disk সীমাবদ্ধতার কারণে পুরো pytest suite কখনো
চালাতেই পারেনি — ফলে `core/__init__.py`-এর eager torch import, `core.auth`-এর
ভুল import, এবং `/health` endpoint-এর stub implementation — এই ৩টা real bug
মাসের পর মাস অলক্ষিত ছিল। প্রতিটা bug আগেরটার আড়ালে লুকানো ছিল।

**নিয়ম:** "CI সবুজ" মানেই "সব ঠিক আছে" না যদি CI নিজেই কখনো সম্পূর্ণ চলতে না পারে
(disk/dependency সমস্যায় আটকে থাকে)। পর্যায়ক্রমে (মাসে অন্তত একবার) একটা পরিষ্কার,
সম্পূর্ণ dependency-installed এনভায়রনমেন্টে পুরো suite চালানো উচিত।

## ৬. দ্রুত সমান্তরাল কমিট চলাকালীন rebase conflict resolve করার সময়

এই রিপোতে একাধিক সেশন/টুল একসাথে কাজ করছে। যদি push করার আগে দেখেন `origin/main`
এগিয়ে গেছে, সবসময় fetch + rebase করুন (force-push না), এবং conflict এলে দুই পক্ষের
fix একই bug-এর সমাধান কিনা যাচাই করুন — প্রায়ই দেখা গেছে অন্য সেশন একই bug আগেই
independently ঠিক করে ফেলেছে।

---

## এই পাসে ঠিক হওয়া নির্দিষ্ট bug (রেফারেন্সের জন্য)

- `core/security/auth_middleware.py`: `is_test_environment` import করা ছিল না এবং
  `ALLOW_TEST_AUTH_BYPASS` কন্ডিশন dispatch লজিকে বসানো ছিল না — এখন ঠিক করা হয়েছে।
- `tests/core/test_auth_security_extension.py` (৩টা টেস্ট) ও
  `tests/test_security_middleware.py` (১টা টেস্ট): উপরের ফিক্সের ফলে তৈরি হওয়া
  bypass-related regression ঠিক করতে explicit `is_test_environment=False` patch
  যোগ করা হয়েছে।
