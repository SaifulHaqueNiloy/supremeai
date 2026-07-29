<details>
<summary><strong>🇧🇩 বাংলা অনুবাদ দেখতে এখানে ক্লিক করুন (Click here for Bangla Translation)</strong></summary>

# সুপ্রিমএআই ২.০

সুপ্রিমএআই ২.০-এ স্বাগতম, সর্বজনীন স্ব-শিক্ষণ এআই এজেন্ট প্ল্যাটফর্ম। এই প্রকল্পটি স্বায়ত্তশাসিত এআই এজেন্ট তৈরি, পরিচালনা এবং স্থাপন করার জন্য একটি ব্যাপক, বহুভাষিক মোনোরিপো।

## 🏛️ আর্কিটেকচার ওভারভিউ

সুপ্রিমএআই হল একটি অত্যাধুনিক সিস্টেম যা একত্রে কাজ করা বেশ কয়েকটি মূল উপাদান নিয়ে গঠিত:

### ১. ব্যাকএন্ড (`supremeai-backend`)
**পাইথন** এবং **ফাস্টএপিআই** দিয়ে তৈরি একটি শক্তিশালী, রোল-ভিত্তিক ইঞ্জিন। এটি সমস্ত এআই অপারেশন এবং অর্কেস্ট্রেশনের কেন্দ্রীয় মস্তিষ্ক হিসাবে কাজ করে।

### ২. ফ্রন্টএন্ড (`supremeai-studio-client`)
এআই ডেভেলপমেন্টের জন্য একটি বৈশিষ্ট্য সমৃদ্ধ আইডিই, যা **রিঅ্যাক্ট**, **ভিট**, এবং **টাইপস্ক্রিপ্ট** দিয়ে তৈরি। এটি একটি ওয়েব অ্যাপ এবং একটি ক্রস-প্ল্যাটফর্ম **ইলেকট্রন** ডেস্কটপ অ্যাপ্লিকেশন উভয় হিসাবে চলে।

### ৩. মোবাইল অ্যাপ (`supremeai_mobile`)
**ফ্লাটার** দিয়ে তৈরি একটি ক্রস-প্ল্যাটফর্ম মোবাইল ক্লায়েন্ট যা যেকোনো স্থান থেকে এআই-এর সাথে ইন্টারঅ্যাক্ট করতে এবং সিস্টেম নিরীক্ষণ করতে দেয়।

</details>

# SupremeAI 2.0

Welcome to SupremeAI 2.0, the Universal Self-Learning AI Agent Platform. This project is a comprehensive, multilingual monorepo for developing, managing, and deploying autonomous AI agents.

## 🌐 Live Application URLs
- **Primary Frontend (Netlify):** [https://tiny-stroopwafel-2d981c.netlify.app](https://tiny-stroopwafel-2d981c.netlify.app)
- **Primary Backend (Render):** [https://supremeai-backend-08zd.onrender.com](https://supremeai-backend-08zd.onrender.com)
- **Secondary Backend (Render):** [https://supremeai-backend-secondary.onrender.com](https://supremeai-backend-secondary.onrender.com)
- *Note: Frontend automatically switches backends if one goes to sleep (Zero-Cost HA Strategy).*

## 🏛️ Architecture Overview

SupremeAI is a sophisticated system composed of several core components working in concert:

### 1. Backend (`supremeai-backend`)
A powerful, role-based engine built with **Python** and **FastAPI**. It serves as the central brain for all AI operations and orchestration.
- **Role-Based Loading:** The server can start in `USER` or `ADMIN` mode, exposing different API endpoints for security and separation of concerns.
- **Polyglot Persistence:** Uses the best database for the job, including **PostgreSQL** (relational), **Redis** (caching/queuing), **Neo4j** (graph), and **Qdrant** (vector search).
- **AI/ML Core:** Integrates a vast stack of AI tools, including `LangChain`, `OpenAI`, `Anthropic`, `scikit-learn`, `XGBoost`, `MLflow`, and `Wandb`.

### 2. Frontend (`supremeai-studio-client`)
A feature-rich IDE for AI development, built with **React**, **Vite**, and **TypeScript**. It runs as both a web app and a cross-platform **Electron** desktop application.
- **IDE Features:** Includes the **Monaco Editor**, an integrated **Xterm.js** terminal, and **React Flow** for visual pipeline construction.
- **In-Browser Environment:** Uniquely, it uses the **WebContainer API** to run a live Node.js environment directly in the browser for a true sandboxed development experience.

### 3. Mobile App (`supremeai_mobile`)
A cross-platform mobile client built with **Flutter** that allows for interacting with the AI and monitoring the system from anywhere.

## ✨ Tech Stack

| Category              | Technologies                                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| **Monorepo**          | `pnpm`, `Turborepo`                                                                                      |
| **Backend**             | `Python`, `FastAPI`, `SQLAlchemy`, `Alembic`, `Poetry`, `uv`                                               |
| **Frontend**            | `React`, `TypeScript`, `Vite`, `Electron`, `React Flow`, `Monaco Editor`, `Xterm.js`                      |
| **Mobile**              | `Flutter`, `Dart`, `Provider`                                                                            |
| **Databases**           | `PostgreSQL`, `Redis`, `Neo4j`, `Qdrant`, `MongoDB`, `Elasticsearch`, `Supabase`, `Firebase`              |
| **AI/ML**               | `LangChain`, `OpenAI`, `Anthropic`, `scikit-learn`, `XGBoost`, `MLflow`, `Wandb`                            |
| **Testing**             | `Pytest` (Backend), `Vitest` (Frontend), `Playwright` (E2E)                                              |
| **CI/CD & Infra**       | `GitHub Actions`, `Docker`, `Render`, `Netlify`, `Firebase`                                                |

## 🚀 Getting Started

### Prerequisites
- **Node.js**: >= 20.0.0
- **pnpm**: >= 9.0.0
- **Python**: >= 3.10 (with `uv` recommended)
- **Flutter SDK** (for mobile development)

### Installation
Clone the repository and install all dependencies using `pnpm`. This single command installs dependencies for the entire monorepo, including the Python backend.

```bash
git clone https://github.com/SaifulHaqueNiloy/supremeai.git
cd supremeai
pnpm install
```

## 💻 Development

Run services using the root `pnpm` scripts.

| Command                             | Description                                            |
| ----------------------------------- | ------------------------------------------------------ |
| `pnpm backend:dev`                  | Start the Python FastAPI backend in development mode.    |
| `pnpm --filter supremeai-studio-client dev` | Start the React web application (Studio).        |
| `pnpm desktop:dev`                  | Start the Electron desktop application in dev mode.  |
| `pnpm mobile:dev`                   | Run the Flutter mobile app.                            |
| `pnpm turbo run build`              | Build all apps and packages in the monorepo.         |


## 🧪 Testing

The project has a comprehensive test suite.

| Command                             | Description                                    |
| ----------------------------------- | ---------------------------------------------- |
| `pnpm backend:test`                 | Run backend unit and integration tests (Pytest). |
| `pnpm --filter supremeai-studio-client test`| Run frontend unit tests (Vitest).          |
| `pnpm test:e2e`                     | Run end-to-end tests for the web apps (Playwright). |
| `pnpm turbo run test`               | Run all test suites across the monorepo.      |


## 📦 Monorepo & Package Management

This project uses **pnpm** and **Turborepo** to manage the multi-package workspace. This improves installation speed, reduces disk usage, and provides powerful build pipeline orchestration.

- **`apps/*`**: Contains the deployable applications (backend, studio, mobile, docs).
- **`packages/*`**: Contains shared libraries (UI components, types, utilities).
- See `turbo.json` and the root `package.json` for build and script definitions.

## 🔒 Security: The AutonoGuard Engine

The AutonoGuard Engine provides autonomous governance with enterprise-grade security. It is built on a "Zero Cost, High Scalability, Zero Breakage" philosophy.

- **JIT OTP Enforcement**: Hash-based OTPs with masked IDs and timing-safe comparison.
- **IP Churn Detection**: Redis-backed IP tracking to detect and block malicious automated attacks.
- **Self-Healing Engine**: Uses a vector database to look up remediations for runtime errors and employs a circuit breaker to prevent cascade failures.
- **Availability Protection**: Fail-closed rate limiting and failure fingerprint persistence that survives restarts.

## 💰 Monthly Operating Cost

This entire platform is engineered to run on free-tier services.

| Service | Cost |
|---------|------|
| GCP Cloud Run | $0 (Always Free tier) |
| Firebase Hosting | $0 (Free tier) |
| Render | $0 (Free 750h/month) |
| Upstash Redis | $0 (Free tier, 10k requests/day) |
| **Total** | **$0/month** |

## ⚙️ Development Config (Pre-commit Hooks)

### English:
To facilitate direct pushes from environments like `github.dev`, the pre-commit hooks in this repository have been temporarily commented out/neutralized in `.pre-commit-config.yaml`.
- To re-enable pre-commit checks, uncomment the `repos:` block inside `.pre-commit-config.yaml` and run `pre-commit install`.

### বাংলা:
`github.dev` এনভায়রনমেন্ট থেকে সরাসরি পুশ করার সুবিধার্থে এই রিপোজিটরির pre-commit hooks সাময়িকভাবে `.pre-commit-config.yaml` ফাইলে কমেন্ট আউট (নিষ্ক্রিয়) করে রাখা হয়েছে।
- পুনরায় pre-commit সচল করতে চাইলে `.pre-commit-config.yaml` ফাইলের `repos:` কমেন্ট অংশটি আনকমেন্ট করুন এবং `pre-commit install` রান করুন।

## 🤝 Contributing

Contributions are welcome! Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the terms of the `LICENSE` file.
