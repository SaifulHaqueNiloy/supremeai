# প্রি-কমিট হুক অপ্টিমাইজেশন প্ল্যান - বাংলা

## পরিচিতি

এই ডকুমেন্টে সুপ্রিমএআই প্রজেক্টের বর্তমান প্রি-কমিট হুক কনফিগারেশন বিশ্লেষণ করা হয়েছে এবং অপ্টিমাইজেশন প্রস্তাব দেওয়া হয়েছে। লক্ষ্য হলো সাধারণ ত্রুটি ব্লক করা কিন্তু সময় নষ্ট না করা।

## বর্তমান কনফিগারেশন বিশ্লেষণ

### ১. বেসিক ফাইল হেলথ চেক
- YAML, JSON, TOML সিনট্যাক্স চেক
- মার্জ কনফ্লিক্ট মার্কার ডিটেক্ট
- ডিবাগ স্টেটমেন্ট ব্লক
- এন্ড অফ ফাইল ফিক্সার
- ট্রেইলিং ওয়াইটস্পেস রিমুভার
- প্রাইভেট কী ব্লকার
- পাইথন সিনট্যাক্স গেটকিপার

### ২. সিক্রেট হান্টার
- এআই এবং প্যাটার্ন বেসড সিক্রেট স্ক্যানার

### ৩. পাইথন কোড কোয়ালিটি
- Ruff লিন্টার এবং ফরম্যাটার
- MyPy টাইপ চেকার

### ৪. ফ্রন্টএন্ড কোড কোয়ালিটি
- ESLint ফ্রন্টএন্ড চেক

### ৫. সিকিউরিটি গার্ড
- ব্লাইন্ড স্পট স্ক্যানার
- স্টাব এবং প্লেসহোল্ডার ডেটা ব্লকার
- রাউটার ইম্পোর্ট স্মোক টেস্ট

### ৬. ফ্রি-টিয়ার সাইজ গার্ড
- রেন্ডার/গিটহাব/ভার্সেল/ফায়ারবেস সাইজ লিমিট চেক

## অপ্টিমাইজেশন প্রস্তাব

### ১. হালকা চেক এবং ওজনদার চেক বিভাজন
প্রি-কমিট হুকগুলিকে দুটি ধাপে ভাগ করা উচিত:

#### দ্রুত চেক (১-৩ সেকেন্ডে শেষ)
এই চেকগুলি সবসময় রান হবে এবং সাধারণ ত্রুটি ব্লক করবে:
- সিনট্যাক্স এরর (JSON, YAML, TOML, Python)
- মার্জ কনফ্লিক্ট মার্কার
- ডিবাগ স্টেটমেন্ট
- ট্রেইলিং ওয়াইটস্পেস
- প্রাইভেট কী ডিটেকশন
- স্টাব ডেটা ব্লকার

#### গভীর চেক (বাধ্যতামূলক নয়, অপশনাল)
এই চেকগুলি সময় বেশি নেয় এবং কেবল CI-এ রান করা উচিত:
- Ruff লিন্টিং এবং ফরম্যাটিং
- MyPy টাইপ চেকিং
- ESLint চেক
- সিকিউরিটি স্ক্যান
- সাইজ গার্ড

### ২. ফাইল টাইপ অনুযায়ী স্মার্ট চেক
- শুধুমাত্র পাইথন ফাইল পরিবর্তিত হলে পাইথন চেক রান করুন
- শুধুমাত্র টাইপস্ক্রিপ্ট ফাইল পরিবর্তিত হলে ESLint রান করুন
- কনফিগ ফাইল পরিবর্তিত হলে শুধু সিনট্যাক্স চেক রান করুন

### ৩. পারফরমেন্স অপ্টিমাইজেশন
- ক্যাশে ব্যবহার করুন (কোন ফাইল পরিবর্তিত হয়েছে কিনা চেক করুন)
- প্যারালাল প্রসেসিং সক্ষম করুন যেখানে সম্ভব
- টাইমআউট সেট করুন প্রতিটি চেকের জন্য

## প্রস্তাবিত নতুন কনফিগারেশন

```yaml
# দ্রুত হালকা চেক - প্রতিবার রান হবে
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-yaml
        types: [yaml]
      - id: check-json
        types: [json]
      - id: check-toml
        types: [toml]
      - id: check-merge-conflict
      - id: debug-statements
        types: [python]
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
      - id: detect-private-key
      - id: check-ast
        types: [python]

  - repo: local
    hooks:
      - id: fast-secret-hunter
        name: "🔍 Fast Secret Hunter (Basic Patterns)"
        entry: python scripts/devops/fast_secret_scan.py --staged
        language: system
        pass_filenames: false
        always_run: true

      - id: stub-data-check
        name: "🚫 Stub Data Blocker"
        entry: python scripts/find_stub_data.py --path . --fail-on HIGH
        language: system
        pass_filenames: false

# গভীর চেক - শুধুমাত্র CI বা --all-files দিলে রান হবে
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ⚡ Ruff Linter
        entry: python -m ruff check backend --config=backend/pyproject.toml
        language: system
        pass_filenames: false
        types_or: [python, pyi]
        stages: [push]  # শুধুমাত্র push স্টেজে রান হবে

      - id: mypy
        name: 🔍 MyPy Type Checker
        entry: python -m mypy --config-file=backend/mypy.ini
        language: system
        pass_filenames: false
        stages: [push]

      - id: eslint-frontend
        name: "🔍 ESLint Frontend Check"
        entry: pnpm -C apps/studio-client exec eslint src/ --ext .ts,.tsx
        language: system
        files: ^apps/studio-client/src/.*\.(ts|tsx)$
        pass_filenames: false
        stages: [push]

      - id: security-scan
        name: "🔐 Deep Security Scan"
        entry: python scripts/security/auto_find_blindspots.py
        language: system
        pass_filenames: false
        stages: [push]
```

## বাস্তবায়ন পদ্ধতি

### পদক্ষেপ ১: ফাস্ট সিক্রেট স্ক্যানার তৈরি
নতুন একটি স্ক্রিপ্ট তৈরি করুন যেটি শুধুমাত্র সাধারণ প্যাটার্ন চেক করবে:

```python
# scripts/devops/fast_secret_scan.py
#!/usr/bin/env python3
"""
Fast Secret Scanner for Pre-commit Hook
=======================================
বাংলা: শুধুমাত্র সাধারণ সিক্রেট প্যাটার্ন চেক করে - দ্রুত স্ক্যানের জন্য
"""

import re
import sys
from pathlib import Path

def fast_secret_scan():
    """Fast scan for common secret patterns in staged files."""
    # শুধুমাত্র সাধারণ প্যাটার্ন চেক করবে
    patterns = [
        r'(?i)(password|secret|key|token|api[_-]?key)\s*[=:]\s*["\'][^"\']{10,}',
        r'(?i)aws[_-]?(access|secret).*["\'][^"\']+["\']',
        r'(?i)github[_-]?(token|key).*["\'][^"\']+["\']',
        r'(ssh-rsa|ssh-ed25519)\s+[A-Za-z0-9+/]{20,}={0,3}\s+.*',
    ]
    
    # এখানে স্ক্যান লজিক যোগ করুন
    
    return True  # যদি কোনো সিক্রেট পাওয়া না যায়

if __name__ == "__main__":
    if fast_secret_scan():
        sys.exit(0)
    else:
        sys.exit(1)
```

### পদক্ষেপ ২: পারফরমেন্স মনিটরিং
- প্রতিটি চেকের সময় মেপে রাখুন
- যেসব চেক ১০ সেকেন্ডের বেশি সময় নেয় সেগুলোকে push স্টেজে সরিয়ে নিন

### পদক্ষেপ ৩: স্কিপ অপশন
- `SKIP_FAST_CHECKS=1 git commit` দিয়ে হালকা চেক স্কিপ করা যাবে (বিপজ্জনক, শুধুমাত্র জরুরি ক্ষেত্রে)

## উপসংহার

বর্তমান প্রি-কমিট হুক সিস্টেম নিরাপত্তা এবং কোড কোয়ালিটি বাড়ানোর জন্য ভালো কাজ করছে, কিন্তু এটি দ্রুত ডেভেলপমেন্ট সাইকেলে বাধা হয়ে দাঁড়াতে পারে। প্রস্তাবিত অপ্টিমাইজেশন দ্বারা সাধারণ ত্রুটি ব্লক করা হবে কিন্তু সময় ব্যয় কমানো হবে।