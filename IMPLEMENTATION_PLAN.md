# SupremeAI 2.0 বাস্তবায়ন পরিকল্পনা

## ১. পরিচিতি

এই বাস্তবায়ন পরিকল্পনা SupremeAI 2.0 প্রকল্পের নিরাপত্তা সমস্যা সমাধান, ব্যবহারকারী পরিষেবা উন্নত করা এবং স্বাধীন এআই এজেন্ট হিসেবে কাজ করার ক্ষমতা বৃদ্ধির জন্য তৈরি করা হয়েছে।

## ২. সমস্যা তালিকা

### ২.১ নিরাপত্তা সমস্যা
- ডবল-স্পেন্ডিং (Double-Spending) ভেক্টর
- AST স্যান্ডবক্স বাইপাস (getattr/hasattr ব্যবহার করে)
- SSRF (Server-Side Request Forgery) ঝুঁকি
- Redis লক ফলব্যাক বাইপাস
- স্ট্রিপ ওয়েবহুক সাইনেচার টাইমিং অ্যাটাক

### ২.২ কর্মক্ষমতা সমস্যা
- ইন-মেমরি রেট লিমিটারে রেস কন্ডিশন
- ফ্লোটিং পয়েন্ট টোকেন ক্যালকুলেশন
- অসীম মেমরি ক্যাশে ডিকশনারি
- স্ট্যাক ট্রেস লিক

### ২.৩ গঠনগত সমস্যা
- অগোছালো ফোল্ডার স্ট্রাকচার
- কোড ডুপ্লিকেশন
- অপর্যাপ্ত ডকুমেন্টেশন

## ৩. বাস্তবায়ন পর্ব

### পর্ব ১: নিরাপত্তা সমস্যা সমাধান (ত্বরিত প্রাথমিক পর্ব)

#### ৩.১.১ ডবল-স্পেন্ডিং প্রতিরোধ
**ফাইল**: `backend/core/llm/token_deductor.py`

```python
def _acquire_distributed_lock(self, lock_key: str, lock_value: str, ttl: int = 10) -> bool:
    """
    একটি বিতরণিত লক Upstash Redis SET ব্যবহার করে অর্জন করে।
    প্রোডাকশনে Redis অনুপস্থিত থাকলে RuntimeError নিক্ষেপ করে (Fail-Closed)।
    """
    if not redis_queue.configured:
        if settings.env in {"production", "staging"}:
            raise RuntimeError("Redis unavailable in production - cannot guarantee idempotency. Fail-Closed.")
        logger.warning("Redis lock not configured - proceeding in test mode only")
        return True

    try:
        return redis_queue.set_nx(lock_key, lock_value, ex=ttl)
    except Exception as e:
        logger.error(f"Failed to acquire distributed lock: {e}")
        if settings.env in {"production", "staging"}:
            raise RuntimeError("Redis lock acquisition failed. Fail-Closed.") from e
        return False
```

#### ৩.১.২ AST স্যান্ডবক্স উন্নতি
**ফাইল**: `backend/core/immune_system.py`

```python
def visit_Call(self, node: ast.Call):
    # ডান্ডার মেথড এক্সেসের মাধ্যমে স্যান্ডবক্স এস্কেপ ব্লক করুন
    if isinstance(node.func, ast.Attribute):
        if node.func.attr in {"__class__", "__bases__", "__subclasses__", "__globals__", "__builtins__", "__dict__", "__mro__", "__code__", "__closure__", "__func__"}:
            raise SecuritySandboxError(f"Sandbox escape via attribute access blocked: {node.func.attr}")
        # getattr() কলগুলো সম্পূর্ণভাবে ব্লক করুন
        if node.func.attr in {"getattr", "hasattr", "setattr", "delattr"}:
            raise SecuritySandboxError(f"Banned reflection function call detected: {node.func.attr}")
        if node.func.attr in {"import_module", "system", "popen", "spawn", "fork", "run", "run_async"}:
            raise SecuritySandboxError(f"Banned method invocation detected: {node.func.attr}")

    # সরাসরি ফাংশন কল ব্লক করুন
    if isinstance(node.func, ast.Name) and node.func.id in self.banned_functions:
        raise SecuritySandboxError(f"Banned function call detected: {node.func.id}")

    self.generic_visit(node)

def visit_Subscript(self, node: ast.Subscript) -> None:
    # ডান্ডার অ্যাট্রিবিউট চেইন চেক রিকার্সিভলি করুন
    if isinstance(node.value, ast.Attribute):
        if node.value.attr in self.banned_attributes:
            raise SecuritySandboxError(f"Dunder attribute access blocked: {node.value.attr}")
    if isinstance(node.value, ast.Name) and node.value.id in {"builtins", "__builtins__"}:
        raise SecuritySandboxError("Sandbox escape via subscript blocked")
    self.generic_visit(node)

def visit_Attribute(self, node: ast.Attribute):
    # স্যান্ডবক্স এস্কেপের জন্য ডান্ডার অ্যাট্রিবিউট অ্যাক্সেস ব্লক করুন
    if node.attr in self.banned_attributes or node.attr in self.banned_functions:
        raise SecuritySandboxError(f"Sandbox escape pattern blocked: {node.attr}")
    # চেইনড অ্যাক্সেস যেমন a.b.c ধরতে ট্রাভার্স করুন
    self.generic_visit(node)
```

#### ৩.১.৩ SSRF প্রতিরোধ
**ফাইল**: `backend/core/sentinel_agent.py`

```python
import re
from urllib.parse import urlparse

ALLOWED_HOSTS = {"localhost", "127.0.0.1"}

def _validate_endpoint_url(url: str) -> bool:
    """অ্যাডমিন-ডিফাইন্ড হোস্ট ভ্যালিডেশন।"""
    try:
        parsed = urlparse(url)
        # file://, gopher:// এবং মেটাডেটা IP ব্লক করুন
        if parsed.scheme in {"file", "gopher"}:
            return False
        if re.match(r"^(169\.254\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)", parsed.hostname or ""):
            return False
        if settings.env in {"production", "staging"}:
            return parsed.hostname in ALLOWED_HOSTS or parsed.hostname.endswith(".supremeai.internal")
        return True
    except Exception:
        return False

# sentinel_agent.py-এর মধ্যে ব্যবহার:
if not _validate_endpoint_url(url):
    logger.critical(f"SSRF Blocked: Attempted access to {url}")
    continue
```

#### ৩.১.৪ Redis লক সমস্যা সমাধান
**ফাইল**: `backend/core/cache/redis_manager.py`

```python
# redis_manager.py-এ Lua স্ক্রিপ্ট যুক্ত করুন
_RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

async def release_idempotency_lock(key: str, lock_value: str) -> bool:
    """সেরা-নিরাপদভাবে lock ডিলিট।"""
    if not redis_manager.client:
        return False
    try:
        result = await redis_manager.client.eval(_RELEASE_LUA, 1, key, lock_value)
        return bool(result)
    except Exception as e:
        logger.error(f"Idempotency lock release failed: {e}")
        return False
```

#### ৩.১.৫ টাইমিং অ্যাটাক প্রতিরোধ
**ফাইল**: `backend/api/routes/payments.py`

```python
import secrets

# webhook_secret None হলে fail-closed
if webhook_secret is None:
    raise RuntimeError("Stripe webhook secret not configured - rejecting all webhooks (Fail-Closed)")

# টাইমিং-সেফ কম্প্যারিজন (যদি কাস্টম ভেরিফিকেশন দরকার হয়)
def _constant_time_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())
```

### পর্ব ২: কর্মক্ষমতা উন্নতি

#### ৩.২.১ ডিস্ট্রিবিউটেড রেট লিমিটার
**ফাইল**: `backend/core/rate_limiter.py`

```python
async def acquire(self, key: str, limit: int, window: int) -> bool:
    if not self._rate_limit_enabled:
        return True
    try:
        client = await self._get_redis()
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        current = results[0]
        return current <= limit
    except Exception as e:
        logger.error(f"Redis rate limiter unavailable: {e}. Blocking requests (Fail-Closed).")
        raise RuntimeError("Rate limiting unavailable - rejecting requests") from e
```

#### ৩.২.২ টোকেন ক্যালকুলেশন উন্নতি
**ফাইল**: `backend/core/llm/token_deductor.py`

```python
from decimal import Decimal

input_rate = Decimal(str(rates["input"]))
output_rate = Decimal(str(rates["output"]))
cost = (Decimal(input_tokens) / Decimal(1000) * input_rate) + (Decimal(output_tokens) / Decimal(1000) * output_rate)
cost = cost.quantize(Decimal("0.000001"))  # ৬ দশমিক স্থান পর্যন্ত ক্যাপ
```

#### ৩.২.৩ ক্যাশে মেমরি ম্যানেজমেন্ট
**ফাইল**: `backend/core/config_cache.py`

```python
# পিরিয়ডিক ক্যাশে ক্লিনআপ টাস্ক
async def _periodic_cache_cleanup(self):
    while True:
        expired_keys = [k for k, v in self._cached_secrets.items() if v.is_expired]
        for k in expired_keys:
            del self._cached_secrets[k]  # মেমোরি থেকে ডিলিট
        await asyncio.sleep(60)  # প্রতি মিনিটে চেক করুন
```

#### ৩.২.৪ স্ট্যাক ট্রেস লিক প্রতিরোধ
**ফাইল**: `backend/api/routes/billing_api.py`

```python
# জেনেরিক মেসেজ ক্লায়েন্টে পাঠান (কখনো ইন্টারনাল তথ্য প্রকাশ করবেন না)
raise HTTPException(status_code=500, detail="Internal server error. Please contact support.") from e
```

### পর্ব ৩: গঠনগত উন্নতি

#### ৩.৩.১ প্রজেক্ট স্ট্রাকচার উন্নতি
নতুন ফোল্ডার স্ট্রাকচার:

```
backend/
├── agents/              # এআই এজেন্টগুলো
│   ├── __init__.py
│   ├── coder_agent.py
│   ├── reasoner_agent.py
│   └── ...
├── api/                 # API রাউটগুলো
│   ├── __init__.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── payments.py
│   │   └── ...
├── core/               # কোর ফাংশনালিটি
│   ├── llm/
│   ├── security/
│   ├── cache/
│   └── ...
├── database/           # ডেটাবেস মডেল ও কুয়েরি
├── memory/             # মেমরি এবং RAG
├── sandbox/            # স্যান্ডবক্স সিকিউরিটি
├── tools/              # বিভিন্ন টুল
└── utils/              # ইউটিলিটি ফাংশন
```

#### ৩.৩.২ কোড ডুপ্লিকেশন সমাধান
**ফাইল**: `backend/tools/common/base_agent.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel


class BaseAgent(ABC):
    """সব এআই এজেন্টের জন্য বেস ক্লাস"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """এজেন্টের মূল কাজ সম্পাদন করে"""
        pass
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """ইনপুট ভ্যালিডেশন করে"""
        return True
    
    async def preprocess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """ইনপুট প্রি-প্রসেস করে"""
        return inputs
    
    async def postprocess(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """আউটপুট পোস্ট-প্রসেস করে"""
        return outputs


class ToolResult(BaseModel):
    """টুল এক্সিকিউশনের ফলাফল"""
    success: bool
    message: str
    data: Dict[str, Any] = {}
    error: str = ""
```

#### ৩.৩.৩ ডকুমেন্টেশন উন্নতি
**ফাইল**: প্রতিটি ফাংশনে ডকস্ট্রিং যোগ করুন

```python
def process_user_request(user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ব্যবহারকারীর ইনপুট প্রসেস করে এবং প্রাসঙ্গিক এআই এজেন্ট সিলেক্ট করে।
    
    Args:
        user_input (str): ব্যবহারকারীর দেওয়া ইনপুট
        context (Dict[str, Any]): বর্তমান কনটেক্সট ডেটা যেমন ইউজার আইডি, সেশন তথ্য ইত্যাদি
    Returns:
        Dict[str, Any]: এআই এজেন্ট থেকে প্রাপ্ত ফলাফল
    """
    # ফাংশন লজিক এখানে
    pass
```

### পর্ব ৪: ব্যবহারকারী পরিষেবা উন্নতি

#### ৩.৪.১ বুদ্ধিমান এআই এজেন্ট রাউটিং
**ফাইল**: `backend/core/orchestration/agent_router.py`

```python
from typing import Dict, Any, List
from enum import Enum
import asyncio
from ..agents.base_agent import BaseAgent


class AgentType(Enum):
    CODER = "coder"
    REASONER = "reasoner"
    BHASHA = "bhasha"
    OPS = "ops"
    ANALYST = "analyst"


class AgentRouter:
    """ব্যবহারকারীর ইনপুট অনুযায়ী সঠিক এআই এজেন্টে রাউট করে"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """সব এজেন্ট ইনিশিয়ালাইজ করে"""
        # এজেন্ট লোড লজিক এখানে
        pass
    
    async def route_request(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """ব্যবহারকারীর ইনপুট অনুযায়ী সঠিক এজেন্টে রাউট করে"""
        agent_type = self._determine_agent_type(user_input)
        
        if agent_type in self.agents:
            agent = self.agents[agent_type]
            processed_input = await agent.preprocess({"input": user_input, **context})
            result = await agent.execute(processed_input)
            return await agent.postprocess(result)
        else:
            # ডিফল্ট এজেন্ট ব্যবহার করে
            default_agent = self.agents.get(AgentType.REASONER)
            if default_agent:
                return await default_agent.execute({"input": user_input, **context})
            else:
                return {"error": "No available agent to handle request"}
    
    def _determine_agent_type(self, user_input: str) -> AgentType:
        """ইনপুট থেকে সঠিক এজেন্ট টাইপ নির্ধারণ করে"""
        user_lower = user_input.lower()
        
        if any(keyword in user_lower for keyword in ["code", "programming", "python", "javascript", "react"]):
            return AgentType.CODER
        elif any(keyword in user_lower for keyword in ["translate", "bengali", "language", "বাংলা"]):
            return AgentType.BHASHA
        elif any(keyword in user_lower for keyword in ["deploy", "docker", "kubernetes", "cloud", "devops"]):
            return AgentType.OPS
        elif any(keyword in user_lower for keyword in ["calculate", "math", "analyze", "data", "sql"]):
            return AgentType.ANALYST
        else:
            return AgentType.REASONER
```

#### ৩.৪.২ কনটেক্সট ম্যানেজমেন্ট
**ফাইল**: `backend/core/context_manager.py`

```python
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from ..database.models import SessionContext


class ContextManager:
    """ব্যবহারকারীর সেশন কনটেক্সট ম্যানেজ করে"""
    
    def __init__(self):
        self.context_ttl = timedelta(hours=1)  # 1 ঘন্টা কনটেক্সট টিকবে
    
    async def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """সেশন থেকে কনটেক্সট পাওয়ার চেষ্টা করে"""
        try:
            session = await SessionContext.get(session_id)
            if session and not self._is_expired(session.created_at, self.context_ttl):
                return session.context_data
            return {}
        except Exception as e:
            # লগ করুন এবং ডিফল্ট কনটেক্সট রিটার্ন করুন
            return {}
    
    async def update_context(self, session_id: str, new_data: Dict[str, Any]) -> bool:
        """সেশনের কনটেক্সট আপডেট করে"""
        try:
            existing_context = await self.get_context(session_id) or {}
            existing_context.update(new_data)
            
            session = SessionContext(
                session_id=session_id,
                context_data=existing_context,
                created_at=datetime.utcnow()
            )
            await session.save()
            return True
        except Exception as e:
            # লগ করুন
            return False
    
    async def clear_context(self, session_id: str) -> bool:
        """সেশনের কনটেক্সট মুছে ফেলে"""
        try:
            await SessionContext.delete(session_id)
            return True
        except Exception as e:
            # লগ করুন
            return False
    
    def _is_expired(self, created_at: datetime, ttl: timedelta) -> bool:
        """কনটেক্সট এক্সপায়ার্ড কিনা চেক করে"""
        return datetime.utcnow() - created_at > ttl
```

#### ৩.৪.৩ ব্যবহারকারী প্রতিক্রিয়া সিস্টেম
**ফাইল**: `backend/core/user_feedback.py`

```python
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import asyncio
from ..database.models import UserFeedback


class FeedbackType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class UserFeedbackSystem:
    """ব্যবহারকারীর প্রতিক্রিয়া সংগ্রহ ও বিশ্লেষণ করে"""
    
    def __init__(self):
        self.feedback_threshold = 5  # প্রতি পাঁচটি ফিডব্যাকে একটি রিপোর্ট তৈরি হবে
        self.feedback_count = 0
    
    async def record_feedback(self, user_id: str, feedback_type: FeedbackType, 
                           query: str, response: str, rating: Optional[int] = None) -> bool:
        """ব্যবহারকারীর প্রতিক্রিয়া রেকর্ড করে"""
        try:
            feedback = UserFeedback(
                user_id=user_id,
                feedback_type=feedback_type.value,
                query=query,
                response=response,
                rating=rating,
                timestamp=datetime.utcnow()
            )
            await feedback.save()
            
            self.feedback_count += 1
            
            # প্রতি কয়েকটি ফিডব্যাকে একটি রিপোর্ট তৈরি করুন
            if self.feedback_count % self.feedback_threshold == 0:
                await self._generate_feedback_report()
            
            return True
        except Exception as e:
            # লগ করুন
            return False
    
    async def _generate_feedback_report(self):
        """ফিডব্যাক রিপোর্ট তৈরি করে এবং সিস্টেম ইমপ্রুভমেন্টে ব্যবহার করে"""
        # ফিডব্যাক বিশ্লেষণ এবং সিস্টেম উন্নতি লজিক এখানে
        pass
    
    async def get_user_sentiment(self, user_id: str) -> Dict[str, Any]:
        """ব্যবহারকারীর সেন্টিমেন্ট এনালাইসিস করে"""
        try:
            feedbacks = await UserFeedback.get_by_user(user_id)
            positive_count = sum(1 for f in feedbacks if f.feedback_type == "positive")
            negative_count = sum(1 for f in feedbacks if f.feedback_type == "negative")
            total = len(feedbacks)
            
            if total == 0:
                return {"sentiment": "neutral", "score": 0.0}
            
            sentiment_score = (positive_count - negative_count) / total
            sentiment_label = "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral"
            
            return {
                "sentiment": sentiment_label,
                "score": sentiment_score,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "total_count": total
            }
        except Exception as e:
            # লগ করুন
            return {"sentiment": "neutral", "score": 0.0}
```

## ৪. বাস্তবায়ন পদক্ষেপ

### ৪.১ প্রথম পদক্ষেপ (ত্বরিত)
১. সমস্ত নিরাপত্তা ফিক্স করুন (পর্ব ১)
২. টোকেন ক্যালকুলেশন ও রেট লিমিটার ঠিক করুন (পর্ব ২)
৩. বেস এজেন্ট ক্লাস তৈরি করুন (পর্ব ৩)

### ৪.২ দ্বিতীয় পদক্ষেপ (২-৪ সপ্তাহ)
১. এজেন্ট রাউটার ইমপ্লিমেন্ট করুন
২. কনটেক্সট ম্যানেজমেন্ট সিস্টেম ইমপ্লিমেন্ট করুন
৩. ফিডব্যাক সিস্টেম ইমপ্লিমেন্ট করুন

### ৪.৩ তৃতীয় পদক্ষেপ (৪-৮ সপ্তাহ)
১. প্রজেক্ট স্ট্রাকচার পুনর্গঠন করুন
২. সমস্ত এজেন্ট বেস ক্লাসে রূপান্তর করুন
৩. ডকুমেন্টেশন সম্পূর্ণ করুন

## ৫. পরীক্ষা ও যাচাই

### ৫.১ নিরাপত্তা পরীক্ষা
- সমস্ত নিরাপত্তা ফিক্সের জন্য ইউনিট টেস্ট লিখুন
- ইন্টিগ্রেশন টেস্ট করুন
- পেনেট্রেশন টেস্ট করুন

### ৫.২ কর্মক্ষমতা পরীক্ষা
- লোড টেস্ট করুন
- স্ট্রেস টেস্ট করুন
- পারফরমেন্স মনিটরিং করুন

### ৫.৩ ব্যবহারকারী পরিষেবা পরীক্ষা
- ইউজার এক্সপেরিয়েন্স টেস্ট করুন
- এআই এজেন্টের নির্ভুলতা পরীক্ষা করুন
- ফিডব্যাক সিস্টেম পরীক্ষা করুন

## ৬. সমাপনি মন্তব্য

এই বাস্তবায়ন পরিকল্পনা অনুসরণ করে SupremeAI 2.0 প্রকল্পটি নিরাপদ, কার্যকর এবং ব্যবহারকারী-বান্ধব হবে। এটি ব্যবহারকারীদের সবচেয়ে বুদ্ধিমানের মতো পরিষেবা দিতে সক্ষম হবে এবং তাদের কমান্ড বা কাজ সম্পন্ন করতে পারবে। প্রকল্পটি স্বাধীন, নিরাপদ ও স্বয়ং-নিরাময় এআই এজেন্ট হিসেবে কাজ করবে যা শূন্য-খরচে চলবে এবং মানুষের হস্তক্ষেপ ন্যূনতম রেখে স্বয়ংক্রিয় কাজ করবে।