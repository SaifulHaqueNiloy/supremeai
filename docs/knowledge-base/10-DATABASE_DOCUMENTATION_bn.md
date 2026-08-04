# সুপ্রিম AI 2.0 — ডাটাবেস ডকুমেন্টেশন

**ভার্সন**: 2.0.0  
**শেষ আপডেট**: 2025-01-04  
**স্ট্যাটাস**: লিভিং ডকুমেন্ট  
**ক্লাসিফিকেশন**: ইন্টার্নাল  

---

## 🗄️ ডাটাবেস ওভারভিউ

সুপ্রিম AI 2.0 **পলিগ্লট পেরসিস্টেন্স আর্কিটেকচার** অনুসরণ করে, যার মানে প্রতিটি নির্দিষ্ট ব্যবহারের ক্ষেত্রে সেরা ডাটাবেস টেকনোলজি ব্যবহার করা হয়। এই পদ্ধতি অপ্টিমাল পারফরম্যান্স, বিশেষায়িত ফিচার এবং ভবিষ্যত-প্রুফ স্কেলিং প্রদান করে।

### ডাটাবেস স্ট্যাক

```mermaid
graph TB
    subgraph "PostgreSQL (Supabase)"
        PG_USERS[Users]
        PG_AGENTS[Agents]
        PG_EXECUTIONS[Executions]
        PG_MEMORIES[Memories]
        PG_AUDIT[Audit Logs]
    end

    subgraph "Redis (Upstash)"
        REDIS_SESSIONS[Sessions]
        REDIS_CACHE[Query Cache]
        REDIS_RATE[Rate Limits]
        REDIS_BLACKLIST[Token Blacklist]
    end

    subgraph "Neo4j (Aura)"
        NEO4J_GRAPH[Knowledge Graph]
        NEO4J_RELATIONS[Relationships]
    end

    subgraph "Qdrant (Cloud)"
        QDRANT_VECTORS[Vector Embeddings]
        QDRANT_SEARCH[Semantic Search]
    end

    subgraph "SQLite (Local)"
        SQLITE_TASKS[Pending Tasks]
    end

    PG_USERS --> REDIS_SESSIONS
    PG_AGENTS --> QDRANT_VECTORS
    PG_MEMORIES --> NEO4J_GRAPH
```

---

## 🐘 PostgreSQL (Supabase)

**উদ্দেশ্য**: প্রাইমারি রিলেশনাল ডাটাবেস

**কানেকশন স্ট্রিং**:
```
postgresql+asyncpg://user:password@host:5432/supremeai
```

**ফিচার**:
- JSONB ফর ফ্লেক্সিবল স্কিমা
- UUIDv7 ফর IDs
- pgvector ফর embeddings (1536 ডাইমেনশন)
- রো-লেভেল সিকিউরিটি
- কানেকশন পুলিং

**ফ্রি টিয়ার**: 500MB স্টোরেজ

---

### মূল টেবিল

#### 1. Users টেবিল

**উদ্দেশ্য**: ইউজার অ্যাকাউন্ট স্টোরেজ

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    roles JSONB DEFAULT '["user"]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

**কলাম**:
| কলাম | টাইপ | নিয়ম | বিবরণ |
|-------|------|-------|--------|
| id | UUID | PK | ইউজার আইডি |
| email | VARCHAR(255) | UNIQUE, NOT NULL | ইমেইল অ্যাড্রেস |
| hashed_password | VARCHAR(255) | NOT NULL | বCrypt হ্যাশড পাসওয়ার্ড |
| roles | JSONB | DEFAULT ['user'] | রোল লিস্ট |
| is_active | BOOLEAN | DEFAULT true | অ্যাকাউন্ট সক্রিয় |
| created_at | TIMESTAMP | DEFAULT now() | নিবন্ধন তারিখ |
| updated_at | TIMESTAMP | DEFAULT now() | আপডেট তারিখ |

**রিলেশন**:
- ১-to-Many: agents
- ১-to-Many: executions
- ১-to-Many: api_keys
- ১-to-Many: audit_logs

---

#### 2. Agents টেবিল

**উদ্দেশ্য**: AI এজেন্ট কনফিগারেশন

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_agents_created_at ON agents(created_at);
```

**কলাম**:
| কলাম | টাইপ | নিয়ম | বিবরণ |
|-------|------|-------|--------|
| id | UUID | PK | এজেন্ট আইডি |
| user_id | UUID | FK → users.id | মালিকানার ইউজার |
| name | VARCHAR(255) | NOT NULL | এজেন্ট নাম |
| description | TEXT | NULL | বিবরণ |
| config | JSONB | NOT NULL | এজেন্ট কনফিগারেশন |
| is_active | BOOLEAN | DEFAULT true | সক্রিয় |
| created_at | TIMESTAMP | DEFAULT now() | তৈরি তারিখ |
| updated_at | TIMESTAMP | DEFAULT now() | আপডেট তারিখ |

**config JSONB স্ট্রাকচার**:
```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 4096,
  "tools": ["web_search", "code_executor"],
  "memory": {
    "enabled": true,
    "type": "cascade",
    "ttl": 3600
  },
  "system_prompt": "You are a helpful assistant..."
}
```

---

#### 3. Executions টেবিল

**উদ্দেশ্য**: এজেন্ট এক্সিকিউশন লগ

```sql
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    user_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(50) NOT NULL,
    input JSONB NOT NULL,
    output JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP,
    duration_ms INTEGER
);

CREATE INDEX idx_executions_agent_id ON executions(agent_id);
CREATE INDEX idx_executions_user_id ON executions(user_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_started_at ON executions(started_at);
```

**কলাম**:
| কলাম | টাইপ | নিয়ম | বিবরণ |
|-------|------|-------|--------|
| id | UUID | PK | এক্সিকিউশন আইডি |
| agent_id | UUID | FK → agents.id | এজেন্ট |
| user_id | UUID | FK → users.id | ইউজার |
| status | VARCHAR(50) | NOT NULL | স্ট্যাটাস (pending, running, completed, failed) |
| input | JSONB | NOT NULL | ইনপুট ডাটা |
| output | JSONB | NULL | আউটপুট ডাটা |
| error | TEXT | NULL | এরর মেসেজ |
| started_at | TIMESTAMP | DEFAULT now() | শুরু |
| completed_at | TIMESTAMP | NULL | শেষ |
| duration_ms | INTEGER | NULL | সময় (মিলিসেকেন্ড) |

---

#### 4. Memories টেবিল

**উদ্দেশ্য**: এজেন্ট মেমরি স্টোরেজ

```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    content TEXT NOT NULL,
    embedding vector(1536),
    memory_type VARCHAR(50) NOT NULL,
    importance FLOAT DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT now(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_agent_id ON memories(agent_id);
CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
```

**কলাম**:
| কলাম | টাইপ | নিয়ম | বিবরণ |
|-------|------|-------|--------|
| id | UUID | PK | মেমরি আইডি |
| user_id | UUID | FK → users.id | ইউজার |
| agent_id | UUID | FK → agents.id | এজেন্ট (NULL = গ্লোবাল) |
| content | TEXT | NOT NULL | মেমরি কনটেন্ট |
| embedding | vector(1536) | NULL | ভেক্টর এমবেডিং |
| memory_type | VARCHAR(50) | NOT NULL | টাইপ (short_term, long_term, experience) |
| importance | FLOAT | DEFAULT 0.5 | গুরুত্ব (0-1) |
| metadata | JSONB | DEFAULT {} | অতিরিক্ত ডাটা |
| created_at | TIMESTAMP | DEFAULT now() | তৈরি |
| expires_at | TIMESTAMP | NULL | মেয়াদ শেষ |

---

#### 5. API Keys টেবিল

**উদ্দেশ্য**: API কী ম্যানেজমেন্ট

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    hashed_key VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    permissions JSONB DEFAULT '[]',
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
```

**কলাম**:
| কলাম | টাইপ | নিয়ম | বিবরণ |
|-------|------|-------|--------|
| id | UUID | PK | API কী আইডি |
| user_id | UUID | FK → users.id | মালিকানার ইউজার |
| name | VARCHAR(255) | NOT NULL | কী নাম |
| hashed_key | VARCHAR(255) | UNIQUE, NOT NULL | HMAC-SHA256 হ্যাশ |
| key_prefix | VARCHAR(20) | NOT NULL | লুকআপ প্রিফিক্স |
| permissions | JSONB | DEFAULT [] | পারমিশন লিস্ট |
| expires_at | TIMESTAMP | NULL | মেয়াদ শেষ |
| last_used_at | TIMESTAMP | NULL | শেষ ব্যবহার |
| usage_count | INTEGER | DEFAULT 0 | ব্যবহার গণনা |
| is_active | BOOLEAN | DEFAULT true | সক্রিয় |
| created_at | TIMESTAMP | DEFAULT now() | তৈরি |

---

#### 6. Audit Logs টেবিল

**উদ্দেশ্য**: ক্রিপ্টোগ্রাফিক অডিট ট্রেইল

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT now(),
    signature VARCHAR(255) NOT NULL
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

**কলাম**:
| কলাম | টাইপ | নিয়ম | বিবরণ |
|-------|------|-------|--------|
| id | UUID | PK | লগ আইডি |
| user_id | UUID | FK → users.id | ইউজার (NULL = সিস্টেম) |
| action | VARCHAR(100) | NOT NULL | অ্যাকশন (create, update, delete) |
| resource_type | VARCHAR(100) | NOT NULL | রিসোর্স টাইপ (agent, user) |
| resource_id | UUID | NULL | রিসোর্স আইডি |
| details | JSONB | DEFAULT {} | বিস্তারিত |
| ip_address | INET | NULL | IP অ্যাড্রেস |
| user_agent | TEXT | NULL | ইউজার এজেন্ট |
| timestamp | TIMESTAMP | DEFAULT now() | সময় |
| signature | VARCHAR(255) | NOT NULL | SHA-256 স্বাক্ষর |

---

## 🔴 Redis (Upstash)

**উদ্দেশ্য**: ক্যাচিং, সেশন, রেট লিমিটিং

**কানেকশন স্ট্রিং**:
```
redis://:password@host:6379
```

**ফিচার**:
- TTL-বেসড এক্সপায়ারেশন
- অ্যাটমিক অপারেশন
- Pub/sub

**ফ্রি টিয়ার**: 10,000 রিকোয়েস্ট/দিন

---

### কী প্যাটার্ন

#### সেশন স্টোরেজ
```
Key: session:{session_id}
TTL: 86400 seconds (24 hours)
Value: JSON
{
  "user_id": "uuid",
  "email": "user@example.com",
  "roles": ["user"],
  "created_at": "2025-01-04T00:00:00Z"
}
```

#### রেট লিমিটিং
```
Key: rate_limit:{user_id}:{minute}
TTL: 60 seconds
Value: INTEGER (কাউন্টার)
```

#### ক্যাচিং
```
Key: cache:{hash}
TTL: 3600 seconds (1 hour)
Value: JSON (API রেসপন্স)
```

#### টোকেন ব্ল্যাকলিস্ট
```
Key: token_blacklist:{jti}
TTL: 86400 seconds (24 hours)
Value: "1"
```

---

## 🕸️ Neo4j (Aura)

**উদ্দেশ্য**: নলেজ গ্রাফের জন্য গ্রাফ ডাটাবেস

**কানেকশন স্ট্রিং**:
```
neo4j://host:7687
```

**ফিচার**:
- Cypher কুয়ারি ল্যাঙ্গুয়েজ
- গ্রাফ অ্যালগরিদম
- রিলেশনশিপ ট্রাভার্সাল

**ফ্রি টিয়ার**: 10,000 নোড

---

### নোড টাইপ

#### User নোড
```cypher
CREATE (u:User {
  id: "uuid",
  email: "user@example.com",
  created_at: "2025-01-04T00:00:00Z"
})
```

#### Agent নোড
```cypher
CREATE (a:Agent {
  id: "uuid",
  name: "My Agent",
  user_id: "uuid",
  created_at: "2025-01-04T00:00:00Z"
})
```

#### Tool নোড
```cypher
CREATE (t:Tool {
  id: "uuid",
  name: "web_search",
  category: "search"
})
```

#### Knowledge নোড
```cypher
CREATE (k:Knowledge {
  id: "uuid",
  content: "Knowledge content",
  embedding: [0.1, 0.2, ...]
})
```

---

### রিলেশনশিপ

```cypher
// ইউজার এজেন্ট তৈরি করে
(u:User)-[:CREATED]->(a:Agent)

// এজেন্ট টুল ব্যবহার করে
(a:Agent)-[:USES]->(t:Tool)

// এজেন্ট মেমরি স্টোর করে
(a:Agent)-[:STORES]->(m:Memory)

// নলেজ রিলেশনশিপ
(k1:Knowledge)-[:RELATED_TO]->(k2:Knowledge)

// এজেন্ট কলাবোরেশন
(a1:Agent)-[:COLLABORATES_WITH]->(a2:Agent)
```

---

## 🔍 Qdrant (Cloud)

**উদ্দেশ্য**: এমবেডিংসের জন্য ভেক্টর ডাটাবেস

**কানেকশন স্ট্রিং**:
```
https://cluster.qdrant.tech
```

**ফিচার**:
- 1536-ডাইমেনশনাল ভেক্টর
- Cosine সিমিলারিটি
- পেলোড ফিল্টারিং
- হরিজন্টাল স্কেলিং

**ফ্রি টিয়ার**: 1GB স্টোরেজ

---

### কালেকশন

#### Memories কালেকশন
```python
{
  "vectors": [0.1, 0.2, ...],  # 1536 dimensions
  "payload": {
    "user_id": "uuid",
    "agent_id": "uuid",
    "content": "Memory content",
    "memory_type": "long_term",
    "importance": 0.8,
    "created_at": "2025-01-04T00:00:00Z"
  }
}
```

#### Knowledge কালেকশন
```python
{
  "vectors": [0.1, 0.2, ...],
  "payload": {
    "user_id": "uuid",
    "content": "Knowledge content",
    "source": "web",
    "category": "technology",
    "created_at": "2025-01-04T00:00:00Z"
  }
}
```

---

## 📊 ডাটাবেস ER Diagram

```mermaid
erDiagram
    USERS ||--o{ AGENTS : owns
    USERS ||--o{ EXECUTIONS : executes
    USERS ||--o{ API_KEYS : has
    USERS ||--o{ AUDIT_LOGS : creates
    USERS ||--o{ MEMORIES : stores
    
    AGENTS ||--o{ EXECUTIONS : has
    AGENTS ||--o{ MEMORIES : stores
    
    USERS {
        uuid id PK
        string email UK
        string hashed_password
        jsonb roles
        boolean is_active
        timestamp created_at
    }
    
    AGENTS {
        uuid id PK
        uuid user_id FK
        string name
        jsonb config
        boolean is_active
        timestamp created_at
    }
    
    EXECUTIONS {
        uuid id PK
        uuid agent_id FK
        uuid user_id FK
        string status
        jsonb input
        jsonb output
        timestamp started_at
    }
    
    MEMORIES {
        uuid id PK
        uuid user_id FK
        uuid agent_id FK
        text content
        vector embedding
        string memory_type
        timestamp created_at
    }
    
    API_KEYS {
        uuid id PK
        uuid user_id FK
        string hashed_key UK
        jsonb permissions
        timestamp expires_at
        boolean is_active
    }
    
    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        string action
        string resource_type
        timestamp timestamp
        string signature
    }
```

---

## 🔄 ডাটাবেস কানেকশন

### কানেকশন পুল কনফিগারেশন

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Usage
async with async_session() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()
```

---

## 📊 ডাটাবেস মাইগ্রেশন

### Alembিক কনফিগারেশন

**ফাইল**: `backend/core/database/migrations/env.py`

```python
from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

### মাইগ্রেশন কমান্ড

```bash
# Create migration
alembic revision --autogenerate -m "Add users table"

# Run migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🔍 ডাটাবেস ভেরিফিকেশন

**ভেরিফাই করার উপায়**:

1. **কানেকশন টেস্ট**:
   ```bash
   curl https://supremeai-backend-08zd.onrender.com/api/v1/health/database
   # Should return: {"status": "healthy", "database": "connected"}
   ```

2. **টেবিল লিস্ট**:
   ```bash
   psql $DATABASE_URL -c "\dt"
   # Should show: users, agents, executions, memories, api_keys, audit_logs
   ```

3. **রেকর্ড কাউন্ট**:
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
   ```

4. **ইনডেক্স চেক**:
   ```bash
   psql $DATABASE_URL -c "\di idx_*"
   # Should show all indexes
   ```

---

## 🔗 সম্পর্কিত ডকুমেন্ট

- [03-ARCHITECTURE_bn.md](03-ARCHITECTURE_bn.md) - সিস্টেম আর্কিটেকচার
- [04-FOLDER_STRUCTURE_bn.md](04-FOLDER_STRUCTURE_bn.md) - ফোল্ডার সংগঠন
- [07-DEPENDENCY_DOCUMENTATION_bn.md](07-DEPENDENCY_DOCUMENTATION_bn.md) - ডিপেন্ডেন্সি
- [11-API_DOCUMENTATION_bn.md](11-API_DOCUMENTATION_bn.md) - API রেফারেন্স

---

## ✅ ডাটাবেস ডকুমেন্টেশন ভেরিফিকেশন

**ভেরিফাই করার উপায়**:

1. **স্কিমা ভেরিফাই**:
   ```bash
   # Check all tables exist
   psql $DATABASE_URL -c "\dt"
   
   # Check table structures
   psql $DATABASE_URL -d supremeai -c "\d users"
   psql $DATABASE_URL -d supremeai -c "\d agents"
   ```

2. **রিলেশন ভেরিফাই**:
   ```bash
   # Check foreign keys
   psql $DATABASE_URL -c "
   SELECT conname, conrelid::regclass, confrelid::regclass 
   FROM pg_constraint 
   WHERE contype = 'f';
   "
   ```

3. **ইনডেক্স ভেরিফাই**:
   ```bash
   # Check indexes
   psql $DATABASE_URL -c "\di"
   ```

---

**ডকুমেন্ট স্ট্যাটাস**: ✅ সম্পূর্ণ এবং ভেরিফাইড  
**পরবর্তী রিভিউ**: 2025-02-04  
**অনার**: ডাটাবেস টিম  
**ক্লাসিফিকেশন**: ইন্টার্নাল