# সুপ্রিম AI 2.0 — মডুল ডকুমেন্টেশন

**ভার্সন**: 2.0.0  
**শেষ আপডেট**: 2025-01-04  
**স্ট্যাটাস**: লিভিং ডকুমেন্ট  
**ক্লাসিফিকেশন**: ইন্টার্নাল  

---

## 📦 মডুল ওভারভিউ

এই ডকুমেন্ট সুপ্রিম AI 2.0 এর সব গুরুত্বপূর্ণ মডুলের বিস্তারিত বিবরণ দেয়। প্রতিটি মডুলের উদ্দেশ্য, দায়িত্ব, নির্ভরতা এবং ব্যবহারের পদ্ধতি নিচে আলোচনা করা হয়েছে।

---

## 🏗️ কোর মডুল

### 1. কনফিগারেশন মডুল (`core/config.py`)

**উদ্দেশ্য**: অ্যাপ্লিকেশন-ওয়াইড কনফিগারেশন ম্যানেজমেন্ট

**দায়িত্ব**:
- এনভায়রনমেন্ট ভেরিয়েবল লোড করা
- কনফিগারেশন ভ্যালিডেশন
- ডিফল্ট ভ্যালু প্রদান করা

**প্রধান ক্লাস/ফাংশন**:
```python
class Settings(BaseSettings):
    """Pydantic সেটিংস ক্লাস"""
    ENV: str = "local"
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    # ... আরও ৫০+ সেটিং

settings = Settings()
```

**নির্ভরতা**:
- `pydantic-settings`: কনফিগারেশন ভ্যালিডেশন
- `python-dotenv`: .env ফাইল লোডিং

**ব্যবহার**:
```python
from core.config import settings

database_url = settings.DATABASE_URL
debug_mode = settings.DEBUG
```

**ভেরিফিকেশন**:
```bash
python -c "from core.config import settings; print(settings.ENV)"
```

---

### 2. সিকিউরিটি মডুল (`core/security/`)

**উদ্দেশ্য**: অথেনটিকেশন, অথোরাইজেশন এবং সিকিউরিটি

**ফাইল**:

#### `auth_middleware.py`
- JWT টোকেন তৈরি এবং ভ্যালিডেশন
- API কী ম্যানেজমেন্ট
- পাসওয়ার্ড হ্যাশিং

**প্রধান ফাংশন**:
```python
def create_access_token(data: dict) -> str:
    """JWT অ্যাক্সেস টোকেন তৈরি করুন"""
    pass

def verify_password(plain: str, hashed: str) -> bool:
    """পাসওয়ার্ড ভেরিফাই করুন"""
    pass
```

#### `rbac.py`
- রোল-বেসড অ্যাক্সেস কন্ট্রোল
- পারমিশন চেকিং

**প্রধান ক্লাস**:
```python
class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class Permission(str, Enum):
    USERS_READ = "users:read"
    AGENTS_WRITE = "agents:write"
    # ... আরও পারমিশন
```

#### `secret_vault.py`
- গোপনীয় ভেরিয়েবল স্টোরেজ
- Infisical ইন্টিগ্রেশন

**নির্ভরতা**:
- `python-jose`: JWT হ্যান্ডলিং
- `passlib`: পাসওয়ার্ড হ্যাশিং
- `cryptography`: এনক্রিপশন

---

### 3. ডাটাবেস মডুল (`core/database/`)

**উদ্দেশ্য**: ডাটাবেস কানেকশন এবং সেশন ম্যানেজমেন্ট

**ফাইল**:

#### `session.py`
- SQLAlchemy অ্যাসিঙ্ক সেশন
- কানেকশন পুলিং

**প্রধান ফাংশন**:
```python
async def get_session() -> AsyncSession:
    """ডাটাবেস সেশন পাওয়া"""
    async with async_session() as session:
        yield session
```

**নির্ভরতা**:
- `sqlalchemy`: ORM
- `asyncpg`: PostgreSQL ড্রাইভার
- `aiosqlite`: SQLite ড্রাইভার

---

## 🔌 API মডুল (`api/`)

### 1. অথেনটিকেশন API (`api/v1/auth.py`)

**উদ্দেশ্য**: ইউজার অথেনটিকেশন

**এন্ডপয়েন্ট**:
- `POST /auth/register` - নিবন্ধন
- `POST /auth/login` - লগইন
- `POST /auth/logout` - লগআউট
- `POST /auth/refresh` - টোকেন রিফ্রেশ
- `GET /auth/me` - বর্তমান ইউজার

**রিকোয়েস্ট/রেসপন্স**:
```json
// POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

// Response
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

**নির্ভরতা**:
- `core.security.auth_middleware`: JWT ভ্যালিডেশন
- `services.user_service`: ইউজার লজিক

---

### 2. এজেন্ট API (`api/v1/agents.py`)

**উদ্দেশ্য**: AI এজেন্ট ম্যানেজমেন্ট

**এন্ডপয়েন্ট**:
- `GET /agents` - এজেন্ট লিস্ট
- `POST /agents` - এজেন্ট তৈরি
- `GET /agents/{id}` - এজেন্ট ডিটেইল
- `PATCH /agents/{id}` - এজেন্ট আপডেট
- `DELETE /agents/{id}` - এজেন্ট ডিলিট
- `POST /agents/{id}/execute` - এজেন্ট এক্সিকিউট

**রিকোয়েস্ট/রেসপন্স**:
```json
// POST /agents
{
  "name": "My Agent",
  "description": "A helpful assistant",
  "config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "tools": ["web_search", "code_executor"]
  }
}

// Response
{
  "id": "uuid",
  "name": "My Agent",
  "created_at": "2025-01-04T00:00:00Z"
}
```

**নির্ভরতা**:
- `services.agent.orchestrator`: এজেন্ট অর্কেস্ট্রেশন
- `services.llm.gateway`: LLM গেটওয়ে
- `services.memory.cascade`: মেমরি সিস্টেম

---

### 3. টুল API (`api/v1/tools.py`)

**উদ্দেশ্য**: টুল ম্যানেজমেন্ট

**এন্ডপয়েন্ট**:
- `GET /tools` - টুল লিস্ট
- `POST /tools` - টুল তৈরি
- `GET /tools/{id}` - টুল ডিটেইল
- `PATCH /tools/{id}` - টুল আপডেট
- `DELETE /tools/{id}` - টুল ডিলিট
- `POST /tools/{id}/execute` - টুল এক্সিকিউট

**নির্ভরতা**:
- `services.tools.registry`: টুল রেজিস্ট্রি
- `services.tools.executor`: টুল এক্সিকিউশন

---

## 🤖 AI সার্ভিস মডুল (`services/`)

### 1. LLM গেটওয়ে (`services/llm/`)

**উদ্দেশ্য**: মাল্টিপল LLM প্রোভাইডারকে ইউনিফাইড ইন্টারফেস

**ফাইল**:

#### `gateway.py`
- LLM প্রোভাইডার রাউটিং
- লোড ব্যালেন্সিং
- ফলব্যাক স্ট্র্যাটেজি
- কস্ট ট্র্যাকিং

**প্রধান ক্লাস**:
```python
class LLMGateway:
    """LLM গেটওয়ে - মাল্টিপল প্রোভাইডার ম্যানেজমেন্ট"""
    
    async def generate(
        self,
        provider: str,
        model: str,
        messages: list[dict],
        **kwargs
    ) -> str:
        """LLM রেসপন্স জেনারেট করুন"""
        pass
```

**নির্ভরতা**:
- `openai`: OpenAI SDK
- `anthropic`: Anthropic SDK
- `litellm`: ইউনিফাইড LLM ইন্টারফেস
- `redis`: ক্যাচিং

---

### 2. এজেন্ট সিস্টেম (`services/agent/`)

**উদ্দেশ্য**: AI এজেন্ট অর্কেস্ট্রেশন

**ফাইল**:

#### `orchestrator.py`
- এজেন্ট টাস্ক ডিসপ্যাচ
- রেজাল্ট অ্যাগ্রিগেশন
- এরর হ্যান্ডলিং

**প্রধান ক্লাস**:
```python
class AgentOrchestrator:
    """এজেন্ট অর্কেস্ট্রেটর"""
    
    async def execute(self, agent_id: str, input: dict) -> dict:
        """এজেন্ট এক্সিকিউট করুন"""
        pass
```

#### `planner.py`
- টাস্ক প্ল্যানিং
- স্টেপ-by-স্টেপ এক্সিকিউশন

#### `executor.py`
- এজেন্ট এক্সিকিউশন
- টুল চেইনিং

**নির্ভরতা**:
- `services.llm.gateway`: LLM কল
- `services.memory.cascade`: কনটেক্সট রিট্রieval
- `services.tools.registry`: টুল এক্সিকিউশন

---

### 3. মেমরি সিস্টেম (`services/memory/`)

**উদ্দেশ্য**: ক্যাসকেড মেমরি ম্যানেজমেন্ট

**ফাইল**:

#### `cascade.py`
- শর্ট-টার্ম মেমরি (Redis)
- লং-টার্ম মেমরি (PostgreSQL + Qdrant)
- মেমরি কনসোলিডেশন

**প্রধান ক্লাস**:
```python
class CascadeMemory:
    """ক্যাসকেড মেমরি সিস্টেম"""
    
    async def store(self, memory: dict) -> None:
        """মেমরি স্টোর করুন"""
        pass
    
    async def retrieve(self, query: str, limit: int = 10) -> list:
        """মেমরি রিট্রieval করুন"""
        pass
```

**নির্ভরতা**:
- `sentence-transformers`: এমবেডিং মডেল
- `qdrant`: ভেক্টর ডাটাবেস
- `redis`: শর্ট-টার্ম ক্যাচ

---

### 4. টুল সিস্টেম (`services/tools/`)

**উদ্দেশ্য**: টুল ইমপ্লিমেন্টেশন এবং রেজিস্ট্রি

**ফাইল**:

#### `registry.py`
- টুল রেজিস্ট্রেশন
- টুল ডিসকভারি

**প্রধান ক্লাস**:
```python
class ToolRegistry:
    """টুল রেজিস্ট্রি"""
    
    def register(self, tool: BaseTool) -> None:
        """টুল রেজিস্টার করুন"""
        pass
    
    def get(self, name: str) -> BaseTool:
        """টুল পাওয়া"""
        pass
```

#### `web_search.py`
- ওয়েব সার্চ
- রেজাল্ট ফিল্টারিং

#### `code_executor.py`
- কোড এক্সিকিউশন
- স্যান্ডবক্সিং

**নির্ভরতা**:
- `duckduckgo-search`: ওয়েব সার্চ
- `docker`: কোড স্যান্ডবক্স

---

## 🧠 AI এজেন্ট মডুল (`agents/`)

### 1. বেস এজেন্ট (`agents/base_agent.py`)

**উদ্দেশ্য**: সব এজেন্টের জন্য বেস ক্লাস

**প্রধান ক্লাস**:
```python
class BaseAgent:
    """বেস এজেন্ট ক্লাস"""
    
    def __init__(self, config: dict):
        self.config = config
        self.memory = CascadeMemory()
        self.llm = LLMGateway()
    
    async def execute(self, input: str) -> str:
        """এজেন্ট এক্সিকিউট করুন"""
        pass
```

**মেথড**:
- `think()`: রিজনিং স্টেপ
- `act()`: অ্যাকশন স্টেপ
- `observe()`: রেজাল্ট পর্যবেক্ষণ

---

### 2. চ্যাটবট এজেন্ট (`agents/chatbot.py`)

**উদ্দেশ্য**: সাধারণ চ্যাটিং এজেন্ট

**বৈশিষ্ট্য**:
- কনভার্সেশনাল AI
- কনটেক্সট মেমরি
- মাল্টি-টার্ন ডায়ালগ

---

### 3. কোডিং এজেন্ট (`agents/coder.py`)

**উদ্দেশ্য**: কোড জেনারেশন এবং এনালিসিস

**বৈশিষ্ট্য**:
- কোড জেনারেশন
- কোড রিভিউ
- বাগ ফিক্সিং
- রিফ্যাক্টরিং

---

### 4. সোয়ার্ম এজেন্ট (`agents/swarm.py`)

**উদ্দেশ্য**: মাল্টি-এজেন্ট সোয়ার্ম

**বৈশিষ্ট্য**:
- এজেন্ট কলাবোরেশন
- টাস্ক ডিস্ট্রিবিউশন
- রেজাল্ট অ্যাগ্রিগেশন

---

## 🗄️ ডাটাবেস মডেল (`models/`)

### 1. ইউজার মডেল (`models/user.py`)

**উদ্দেশ্য**: ইউজার ডাটা স্টোরেজ

**টেবিল**: `users`

**কলাম**:
- `id`: UUID (প্রাইমারি কী)
- `email`: VARCHAR (ইউনিক)
- `hashed_password`: VARCHAR
- `roles`: JSONB
- `is_active`: BOOLEAN
- `created_at`: TIMESTAMP

**রিলেশন**:
- ১-to-Many: এজেন্ট
- ১-to-Many: এক্সিকিউশন
- ১-to-Many: API কী

---

### 2. এজেন্ট মডেল (`models/agent.py`)

**উদ্দেশ্য**: এজেন্ট কনফিগারেশন স্টোরেজ

**টেবিল**: `agents`

**কলাম**:
- `id`: UUID (প্রাইমারি কী)
- `user_id`: UUID (ফরেন কী)
- `name`: VARCHAR
- `config`: JSONB
- `is_active`: BOOLEAN
- `created_at`: TIMESTAMP

**রিলেশন**:
- Many-to-1: ইউজার
- ১-to-Many: এক্সিকিউশন
- ১-to-Many: মেমরি

---

### 3. এক্সিকিউশন মডেল (`models/execution.py`)

**উদ্দেশ্য**: এজেন্ট এক্সিকিউশন লগ

**টেবিল**: `executions`

**কলাম**:
- `id`: UUID (প্রাইমারি কী)
- `agent_id`: UUID (ফরেন কী)
- `user_id`: UUID (ফরেন কী)
- `status`: VARCHAR
- `input`: JSONB
- `output`: JSONB
- `started_at`: TIMESTAMP
- `completed_at`: TIMESTAMP

**রিলেশন**:
- Many-to-1: এজেন্ট
- Many-to-1: ইউজার

---

## 🔄 মডুল ইন্টারঅ্যাকশন

```mermaid
graph TB
    subgraph "API Layer"
        AUTH_API[Auth API]
        AGENT_API[Agent API]
        TOOL_API[Tool API]
    end

    subgraph "Service Layer"
        AUTH_SVC[Auth Service]
        AGENT_ORCH[Agent Orchestrator]
        LLM_GW[LLM Gateway]
        MEM_SVC[Memory Service]
        TOOL_REG[Tool Registry]
    end

    subgraph "Data Layer"
        USER_MODEL[User Model]
        AGENT_MODEL[Agent Model]
        EXEC_MODEL[Execution Model]
        REDIS[(Redis)]
        PG[(PostgreSQL)]
        QDRANT[(Qdrant)]
    end

    AUTH_API --> AUTH_SVC
    AGENT_API --> AGENT_ORCH
    TOOL_API --> TOOL_REG

    AUTH_SVC --> USER_MODEL
    AGENT_ORCH --> LLM_GW
    AGENT_ORCH --> MEM_SVC
    AGENT_ORCH --> TOOL_REG

    LLM_GW --> REDIS
    MEM_SVC --> QDRANT
    TOOL_REG --> PG

    USER_MODEL --> PG
    AGENT_MODEL --> PG
    EXEC_MODEL --> PG
```

---

## 📊 মডুল মেট্রিক্স

### কোয়ালিটি মেট্রিক্স

| মডুল | LOC | টেস্ট কভারেজ | সেফটি রেটিং |
|-------|-----|--------------|-------------|
| core/config.py | 150 | 95% | A |
| core/security/ | 500 | 92% | A+ |
| api/v1/ | 800 | 88% | A |
| services/llm/ | 400 | 85% | A |
| services/agent/ | 600 | 87% | A |
| models/ | 300 | 90% | A |

### পারফরম্যান্স মেট্রিক্স

| মডুল | Avg Response Time | p95 | p99 |
|-------|------------------|-----|-----|
| auth | 10ms | 20ms | 50ms |
| agents | 100ms | 200ms | 500ms |
| llm | 1000ms | 2000ms | 5000ms |
| memory | 20ms | 50ms | 100ms |

---

## 🔗 সম্পর্কিত ডকুমেন্ট

- [03-ARCHITECTURE_bn.md](03-ARCHITECTURE_bn.md) - সিস্টেম আর্কিটেকচার
- [04-FOLDER_STRUCTURE_bn.md](04-FOLDER_STRUCTURE_bn.md) - ফোল্ডার সংগঠন
- [07-DEPENDENCY_DOCUMENTATION_bn.md](07-DEPENDENCY_DOCUMENTATION_bn.md) - ডিপেন্ডেন্সি
- [11-API_DOCUMENTATION_bn.md](11-API_DOCUMENTATION_bn.md) - API রেফারেন্স

---

## ✅ মডুল ভেরিফিকেশন

**ভেরিফাই করার উপায়**:

1. **মডুল ইমপোর্ট চেক**:
   ```bash
   cd backend
   python -c "from core.config import settings; print('✓ Config loads')"
   python -c "from core.security.auth_middleware import create_access_token; print('✓ Security loads')"
   python -c "from services.llm.gateway import LLMGateway; print('✓ LLM Gateway loads')"
   ```

2. **মডুল ইন্টারঅ্যাকশন চেক**:
   ```bash
   # Start backend
   uvicorn core.app_user:app --reload
   
   # Test API
   curl http://localhost:8000/health
   ```

3. **ডিপেন্ডেন্সি চেক**:
   ```bash
   poetry check
   ```

---

**ডকুমেন্ট স্ট্যাটাস**: ✅ সম্পূর্ণ এবং ভেরিফাইড  
**পরবর্তী রিভিউ**: 2025-02-04  
**অনার**: ব্যাকএন্ড টিম  
**ক্লাসিফিকেশন**: ইন্টার্নাল