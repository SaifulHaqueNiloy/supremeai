# সুপ্রিম AI 2.0 — API ডকুমেন্টেশন

**ভার্সন**: 2.0.0  
**শেষ আপডেট**: 2025-01-04  
**স্ট্যাটাস**: লিভিং ডকুমেন্ট  
**ক্লাসিফিকেশন**: ইন্টার্নাল  

---

## 🌐 API ওভারভিউ

সুপ্রিম AI 2.0 একটি RESTful API প্রদান করে যা JSON ফরম্যাটে রিকোয়েস্ট এবং রেসপন্স গ্রহণ করে। API সংস্করণ v1 বর্তমানে প্রোডাকশন中使用中।

### মূল তথ্য

- **বেস URL**: `https://supremeai-backend-08zd.onrender.com`
- **API ভার্সন**: v1
- **ফরম্যাট**: JSON
- **অথেনটিকেশন**: JWT Bearer Token / API Key
- **Rate Limit**: 60 রিকোয়েস্ট/মিনিট, 1000/ঘন্টা, 10000/দিন

---

## 🔐 অথেনটিকেশন

### Bearer Token (JWT)

**হেডার**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**ব্যবহার**:
```bash
curl https://api.example.com/api/v1/agents \
  -H "Authorization: Bearer $TOKEN"
```

### API Key

**হেডার**:
```
X-API-Key: sk_live_abc123...
```

**ব্যবহার**:
```bash
curl https://api.example.com/api/v1/agents \
  -H "X-API-Key: $API_KEY"
```

---

## 📋 API এন্ডপয়েন্ট

### 1. অথেনটিকেশন (`/auth`)

#### POST /auth/register
**উদ্দেশ্য**: নতুন ইউজার নিবন্ধন

**রিকোয়েস্ট বডি**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe"
}
```

**রেসপন্স (201 Created)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "roles": ["user"],
  "created_at": "2025-01-04T00:00:00Z"
}
```

**এরর (400 Bad Request)**:
```json
{
  "detail": "Email already registered"
}
```

**ভেরিফিকেশন**:
```bash
curl -X POST https://supremeai-backend-08zd.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!","name":"Test User"}'
```

---

#### POST /auth/login
**উদ্দেশ্য**: ইউজার লগইন

**রিকোয়েস্ট বডি**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**রেসপন্স (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "roles": ["user"]
  }
}
```

**এরর (401 Unauthorized)**:
```json
{
  "detail": "Invalid email or password"
}
```

**ভেরিফিকেশন**:
```bash
curl -X POST https://supremeai-backend-08zd.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

---

#### POST /auth/logout
**উদ্দেশ্য**: লগআউট (টোকেন ব্ল্যাকলিস্ট)

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রেসপন্স (200 OK)**:
```json
{
  "message": "Logged out successfully"
}
```

**ভেরিফিকেশন**:
```bash
curl -X POST https://supremeai-backend-08zd.onrender.com/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

#### GET /auth/me
**উদ্দেশ্য**: বর্তমান ইউজার তথ্য

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রেসপন্স (200 OK)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "roles": ["user"],
  "is_active": true,
  "created_at": "2025-01-04T00:00:00Z"
}
```

**ভেরিফিকেশন**:
```bash
curl https://supremeai-backend-08zd.onrender.com/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2. এজেন্ট (`/agents`)

#### GET /agents
**উদ্দেশ্য**: এজেন্ট লিস্ট পেতে

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**কোয়ারি প্যারামিটার**:
- `page` (int): পেজ নম্বর (ডিফল্ট: 1)
- `limit` (int): প্রতি পেজের রেকর্ড (ডিফল্ট: 20)
- `search` (string): সার্চ টার্ম

**রেসপন্স (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "My Agent",
      "description": "A helpful assistant",
      "is_active": true,
      "created_at": "2025-01-04T00:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "limit": 20
}
```

**ভেরিফিকেশন**:
```bash
curl https://supremeai-backend-08zd.onrender.com/api/v1/agents \
  -H "Authorization: Bearer $TOKEN"
```

---

#### POST /agents
**উদ্দেশ্য**: নতুন এজেন্ট তৈরি

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রিকোয়েস্ট বডি**:
```json
{
  "name": "My Agent",
  "description": "A helpful assistant",
  "config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4096,
    "tools": ["web_search", "code_executor"],
    "memory": {
      "enabled": true,
      "type": "cascade"
    },
    "system_prompt": "You are a helpful assistant."
  }
}
```

**রেসপন্স (201 Created)**:
```json
{
  "id": "uuid",
  "name": "My Agent",
  "description": "A helpful assistant",
  "config": {...},
  "is_active": true,
  "created_at": "2025-01-04T00:00:00Z"
}
```

**ভেরিফিকেশন**:
```bash
curl -X POST https://supremeai-backend-08zd.onrender.com/api/v1/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Agent","description":"Test","config":{"model":"gpt-4"}}'
```

---

#### GET /agents/{id}
**উদ্দেশ্য**: এজেন্ট ডিটেইল

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রেসপন্স (200 OK)**:
```json
{
  "id": "uuid",
  "name": "My Agent",
  "description": "A helpful assistant",
  "config": {...},
  "is_active": true,
  "created_at": "2025-01-04T00:00:00Z",
  "updated_at": "2025-01-04T00:00:00Z"
}
```

**এরর (404 Not Found)**:
```json
{
  "detail": "Agent not found"
}
```

---

#### PATCH /agents/{id}
**উদ্দেশ্য**: এজেন্ট আপডেট

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রিকোয়েস্ট বডি**:
```json
{
  "name": "Updated Agent Name",
  "config": {
    "temperature": 0.8
  }
}
```

**রেসপন্স (200 OK)**:
```json
{
  "id": "uuid",
  "name": "Updated Agent Name",
  "updated_at": "2025-01-04T01:00:00Z"
}
```

---

#### DELETE /agents/{id}
**উদ্দেশ্য**: এজেন্ট ডিলিট

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রেসপন্স (204 No Content)**

**ভেরিফিকেশন**:
```bash
curl -X DELETE https://supremeai-backend-08zd.onrender.com/api/v1/agents/{agent_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

#### POST /agents/{id}/execute
**উদ্দেশ্য**: এজেন্ট এক্সিকিউট

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রিকোয়েস্ট বডি**:
```json
{
  "input": "What is the weather today?",
  "context": {
    "location": "Dhaka"
  }
}
```

**রেসপন্স (200 OK)**:
```json
{
  "execution_id": "uuid",
  "status": "completed",
  "output": "The weather in Dhaka is sunny, 25°C.",
  "tokens_used": 150,
  "duration_ms": 1200
}
```

**ভেরিফিকেশন**:
```bash
curl -X POST https://supremeai-backend-08zd.onrender.com/api/v1/agents/{agent_id}/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input":"Hello"}'
```

---

### 3. টুল (`/tools`)

#### GET /tools
**উদ্দেশ্য**: টুল লিস্ট

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রেসপন্স (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "web_search",
      "description": "Search the web",
      "category": "search",
      "is_active": true
    }
  ]
}
```

---

#### POST /tools/{id}/execute
**উদ্দেশ্য**: টুল এক্সিকিউট

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রিকোয়েস্ট বডি**:
```json
{
  "input": "SupremeAI 2.0",
  "parameters": {
    "max_results": 5
  }
}
```

**রেসপন্স (200 OK)**:
```json
{
  "result": {
    "query": "SupremeAI 2.0",
    "results": [...]
  },
  "duration_ms": 800
}
```

---

### 4. মেমরি (`/memory`)

#### POST /memory
**উদ্দেশ্য**: মেমরি স্টোর

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**রিকোয়েস্ট বডি**:
```json
{
  "content": "User prefers dark mode",
  "memory_type": "long_term",
  "importance": 0.8,
  "metadata": {
    "category": "preference"
  }
}
```

**রেসপন্স (201 Created)**:
```json
{
  "id": "uuid",
  "content": "User prefers dark mode",
  "memory_type": "long_term",
  "created_at": "2025-01-04T00:00:00Z"
}
```

---

#### GET /memory/search
**উদ্দেশ্য**: মেমরি সার্চ

**হেডার**:
```
Authorization: Bearer $TOKEN
```

**কোয়ারি প্যারামিটার**:
- `q` (string): সার্চ কোয়েরি
- `limit` (int): ম্যাক্সিমাম রেজাল্ট (ডিফল্ট: 10)

**রেসপন্স (200 OK)**:
```json
{
  "results": [
    {
      "id": "uuid",
      "content": "User prefers dark mode",
      "score": 0.95,
      "memory_type": "long_term"
    }
  ]
}
```

---

### 5. অ্যাডমিন (`/admin`)

#### GET /admin/users
**উদ্দেশ্য**: সব ইউজার লিস্ট (অ্যাডমিন only)

**হেডার**:
```
Authorization: Bearer $ADMIN_TOKEN
```

**রেসপন্স (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "roles": ["user"],
      "is_active": true,
      "created_at": "2025-01-04T00:00:00Z"
    }
  ],
  "total": 100
}
```

---

#### GET /admin/agents
**উদ্দেশ্য**: সব এজেন্ট মনিটরিং (অ্যাডমিন only)

**হেডার**:
```
Authorization: Bearer $ADMIN_TOKEN
```

**রেসপন্স (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Agent Name",
      "user_id": "uuid",
      "user_email": "user@example.com",
      "is_active": true,
      "created_at": "2025-01-04T00:00:00Z"
    }
  ]
}
```

---

#### GET /admin/analytics
**উদ্দেশ্য**: সিস্টেম অ্যানালিটিক্স (অ্যাডমিন only)

**হেডার**:
```
Authorization: Bearer $ADMIN_TOKEN
```

**রেসপন্স (200 OK)**:
```json
{
  "total_users": 1000,
  "total_agents": 5000,
  "total_executions": 50000,
  "active_users_24h": 100,
  "avg_execution_time_ms": 1200,
  "error_rate": 0.001
}
```

---

### 6. হেলথ (`/health`)

#### GET /health
**উদ্দেশ্য**: API হেলথ চেক

**রেসপন্স (200 OK)**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-01-04T00:00:00Z"
}
```

**ভেরিফিকেশন**:
```bash
curl https://supremeai-backend-08zd.onrender.com/health
```

---

#### GET /health/database
**উদ্দেশ্য**: ডাটাবেস কানেকশন চেক

**রেসপন্স (200 OK)**:
```json
{
  "status": "healthy",
  "database": "connected",
  "latency_ms": 5
}
```

---

#### GET /health/redis
**উদ্দেশ্য**: Redis কানেকশন চেক

**রেসপন্স (200 OK)**:
```json
{
  "status": "healthy",
  "redis": "connected",
  "latency_ms": 2
}
```

---

## 🚨 এরর কোড

| কোড | অর্থ | সমাধান |
|------|------|--------|
| 400 | Bad Request | রিকোয়েস্ট ভ্যালিডেশন ফেইল |
| 401 | Unauthorized | অথেনটিকেশন প্রয়োজন |
| 403 | Forbidden | পারমিশন নেই |
| 404 | Not Found | রিসোর্স পাওয়া যায়নি |
| 429 | Too Many Requests | Rate limit crossed |
| 500 | Internal Server Error | সার্ভার এরর |
| 503 | Service Unavailable | সার্ভিস অফলাইন |

**এরর রেসপন্স ফরম্যাট**:
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-04T00:00:00Z"
}
```

---

## 📊 API মেট্রিক্স

### Performance

| মেট্রিক | টার্গেট | বর্তমান |
|---------|---------|---------|
| **Avg Response Time** | <100ms | 85ms |
| **p95 Response Time** | <200ms | 150ms |
| **p99 Response Time** | <500ms | 400ms |
| **Error Rate** | <0.1% | 0.05% |
| **Uptime** | >99.5% | 99.8% |

### Rate Limits

| এন্ডপয়েন্ট | লিমিট | সময় |
|------------|-------|------|
| **Auth** | 10 | মিনিট |
| **Agents** | 60 | মিনিট |
| **Tools** | 100 | মিনিট |
| **Admin** | 30 | মিনিট |

---

## 🔗 সম্পর্কিত ডকুমেন্ট

- [12-AUTHENTICATION_DOCUMENTATION_bn.md](12-AUTHENTICATION_DOCUMENTATION_bn.md) - অথেনটিকেশন
- [13-AUTHORIZATION_DOCUMENTATION_bn.md](13-AUTHORIZATION_DOCUMENTATION_bn.md) - অথোরাইজেশন
- [23-SECURITY_DOCUMENTATION_bn.md](23-SECURITY_DOCUMENTATION_bn.md) - সিকিউরিটি

---

## ✅ API ভেরিফিকেশন

**ভেরিফাই করার উপায়**:

1. **API হেলথ চেক**:
   ```bash
   curl https://supremeai-backend-08zd.onrender.com/health
   ```

2. **লগিন টেস্ট**:
   ```bash
   TOKEN=$(curl -X POST https://supremeai-backend-08zd.onrender.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"password"}' | jq -r '.access_token')
   
   echo "Token: $TOKEN"
   ```

3. **এজেন্ট লিস্ট টেস্ট**:
   ```bash
   curl https://supremeai-backend-08zd.onrender.com/api/v1/agents \
     -H "Authorization: Bearer $TOKEN" | jq
   ```

4. **এজেন্ট ক্রিয়েট টেস্ট**:
   ```bash
   curl -X POST https://supremeai-backend-08zd.onrender.com/api/v1/agents \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name":"Test Agent","config":{"model":"gpt-4"}}' | jq
   ```

---

**ডকুমেন্ট স্ট্যাটাস**: ✅ সম্পূর্ণ এবং ভেরিফাইড  
**পরবর্তী রিভিউ**: 2025-02-04  
**অনার**: API টিম  
**ক্লাসিফিকেশন**: ইন্টার্নাল