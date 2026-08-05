# SupremeAI 2.0 — Local ↔ GitHub CI-Parity Hooks

## অডিট ফলাফল (Audit Findings)

`main` branch clone করে `.pre-commit-config.yaml` কে
`.github/workflows/supreme-core-ci.yml`-এর `pre-merge-gate` জবের সাথে
লাইন-বাই-লাইন মিলিয়ে দেখা হয়েছে। বেশিরভাগ গেট আগে থেকেই local এ ছিল
(stub-data, blindspot scan, ruff, mypy, router-smoke-test, eslint,
free-tier guard) — কিন্তু GitHub-এ চলা ৩টি গেট local এ ছিল না, তাই একটি
কমিট local এ ক্লিন পাস করেও GitHub-এ ফেল হতে পারত:

| গেট | GitHub-এ ছিল | Local-এ ছিল (আগে) |
|---|---|---|
| Gate 3.5 — Admin Router Auth Lint Guard | ✅ | ❌ |
| Gate 3 — httpx.AsyncClient() timeout audit | ✅ | ❌ |
| Observability Audit (silent except / print) | ✅ | ❌ |

এছাড়া pytest coverage gate (`--cov-fail-under=38`) ও পুরো frontend
turbo build+lint+vitest পাইপলাইন কোনো local hook-এই ছিল না — এগুলো
`git commit`-এ চালালে প্রতিটি কমিট মিনিটের পর মিনিট আটকে থাকত, তাই এগুলো
**pre-push**-এ রাখা হয়েছে, commit-এ নয়।

## দুই-স্তর ডিজাইন (Two-Layer Design)

```
git commit  →  .pre-commit-config.yaml   (সেকেন্ডে শেষ — static checks only)
git push    →  .git/hooks/pre-push       (CI-এর সাথে হুবহু মিল — ruff, mypy,
                                           admin-auth guard, httpx audit,
                                           observability audit, free-tier guard,
                                           + backend/frontend tests if changed)
```

এই বিভাজনের কারণ: commit ঘন ঘন হয় (fast থাকা জরুরি), push তুলনামূলক কম হয়
এবং push-ই আসলে GitHub Actions ট্রিগার করে — তাই ভারী চেকগুলো এখানেই
সবচেয়ে বেশি মূল্য দেয়।

## ইনস্টল

1. `pre-push`, `setup-git-hooks.sh`, এবং (চাইলে) `pre-commit-config.yaml`
   — এই তিনটি ফাইল একই ফোল্ডারে ডাউনলোড করুন।
2. রিপোর যেকোনো জায়গা থেকে চালান:
   ```bash
   bash setup-git-hooks.sh
   ```
   এটি `pre-push` কে `.git/hooks/pre-push`-এ কপি করবে, executable করবে,
   এবং `pre-commit` framework ইনস্টল থাকলে সেটাও রি-ইনস্টল করবে।
3. (ঐচ্ছিক কিন্তু সুপারিশকৃত) repo-র root-এ থাকা `.pre-commit-config.yaml`-কে
   এই বান্ডেলের `pre-commit-config.yaml` দিয়ে replace করুন — এতে ৩টি
   missing গেট commit-time এও চলবে (এগুলো grep/AST-ভিত্তিক, প্রতিটি <2 সেকেন্ড)।

## দৈনন্দিন ব্যবহার

- স্বাভাবিক `git commit` এবং `git push` — কিছুই আলাদা করতে হবে না।
- `pre-push` শুধু পরিবর্তিত অংশ (backend/frontend) অনুযায়ী চেক চালায় —
  শুধু docs পরিবর্তন করলে কিছুই চলবে না, সময় নষ্ট হবে না।
- ডিফল্টে পুরো pytest suite (DB/Redis দরকার) চলে না — শুধু
  `pytest --collect-only` (import/syntax এরর সেকেন্ডে ধরে)। কোনো বড় push-এর
  আগে CI-এর মতো পুরো suite + coverage gate চালাতে চাইলে:
  ```bash
  RUN_FULL_TESTS=1 git push
  ```
  (এর জন্য local এ postgres:5432 ও redis:6379 রানিং থাকতে হবে।)
- সত্যিই জরুরি অবস্থায় গেট বাইপাস করতে:
  ```bash
  SKIP_CI_PARITY=1 git push
  # অথবা
  git push --no-verify
  ```
  (এতেও GitHub Actions অবশ্যই চলবে ও আসল ফলাফল দেবে — শুধু local গেট স্কিপ হয়।)

## কেন "80–90%"

CodeQL/Trivy security scanning এবং Render/Vercel/Firebase deploy জবগুলো
(network/credential-নির্ভর, sandbox/secrets ছাড়া রিপ্রোডিউস অযোগ্য) এই
hook-এর কভারেজের বাইরে রয়ে গেছে — তাই ১০০% নয়, তবে বাকি সব কোড-কোয়ালিটি ও
টেস্ট গেট (যেগুলো বাস্তবে বেশিরভাগ CI ফেইলের কারণ) এখন local এও চলে।
