# Part 14: Cloud Infrastructure, Edge Workers & Docker Prod Audit

> **Audit Generation Time:** `2026-07-24 20:09:08 UTC`  
> **Module Description:** Terraform, Cloudflare Worker JS, Firebase Functions, Docker Prod, and deployment specs.  
> **Status:** `SELF_CONTAINED / READY FOR EXTERNAL AI AUDIT`

---

## 1. 📁 Target Subsystems & File Inventory

- `infrastructure/` (Directory, 58 files)
- `cloudflare-worker/` (Directory, 2 files)
- `Dockerfile` (File, 1887 bytes)
- `render.yaml` (File, 7348 bytes)
- `vercel.json` (File, 1455 bytes)

---

## 2. 🔍 Audit Objectives & Key Checklist

- [ ] **Code Quality & Type Safety:** Check MyPy type hints and Ruff linting rules.
- [ ] **Security & Resilience:** Check exception handling, circuit breakers, and rate limiters.
- [ ] **Zero-Cost & Free-Tier Optimization:** Ensure no paid cloud service dependencies.
- [ ] **Bangla Code Comments:** Verify `// বাংলা মন্তব্য` is present across updated code blocks.

---

## 3. 📦 Complete Subsystem Source Code Dump

Below is the full source code for all target files in this module. Any external AI can audit this single document directly.

### 📄 `infrastructure/check_deploy_gate.py`

```py
import sys
from google.cloud import firestore
from loguru import logger


def verify_deployment_gate():
    logger.info(
        "🔍 CI/CD Gatekeeper: Auditing SupremeAI 2.0 autonomous deployment gate status..."
    )

    try:
        db = firestore.Client()
        gate_ref = db.collection("deploy_gate").document("status")
        doc = gate_ref.get()

        if not doc.exists:
            logger.warning(
                "⚠️ Deploy gate status document not found. Defaulting to SAFE/UNLOCKED."
            )
            sys.exit(0)

        gate_data = doc.to_dict()
        status = gate_data.get("status", "UNLOCKED").upper()
        reason = gate_data.get("reason", "No reason provided.")
        updated_at = gate_data.get("updated_at", "Unknown time")

        if status == "LOCKED":
            logger.critical("❌" * 20)
            logger.critical("🚨 DEPLOYMENT REJECTED! The autonomous gate is LOCKED.")
            logger.critical(f"📝 Reason: {reason}")
            logger.critical(f"⏰ Last Audit Update: {updated_at}")
            logger.critical("❌" * 20)
            # Exit code 1 দিয়ে সিআই/সিডি পাইপলাইনকে এখানেই থামিয়ে দেওয়া হবে
            sys.exit(1)

        logger.info(
            f"🟢 DEPLOYMENT APPROVED. Autonomous gate status is UNLOCKED. (Reason: {reason})"
        )
        sys.exit(0)

    except Exception as e:
        logger.critical(
            f"⚠️ Gatekeeper failed to query Firestore: {str(e)}. Locking deployment for safety."
        )
        sys.exit(1)


if __name__ == "__main__":
    verify_deployment_gate()

```

### 📄 `infrastructure/cloudflare_worker.js`

```js
// Architectural Fix: In-memory circuit breaker state
const circuitBreakerState = {
  brokenUntil: 0, // Timestamp until which the circuit is open
  failureCount: 0,
  lastFailureTime: 0,
};

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

addEventListener('scheduled', event => {
  event.waitUntil(checkHealthAndStore())
})

function getKV() {
  if (typeof env !== 'undefined' && env.SUPREMEAI_KV) return env.SUPREMEAI_KV;
  if (typeof SUPREMEAI_KV !== 'undefined') return SUPREMEAI_KV;
  if (typeof globalThis !== 'undefined' && globalThis.SUPREMEAI_KV) return globalThis.SUPREMEAI_KV;
  return null;
}

function getBackends() {
  const gcp_url = typeof env !== 'undefined' ? env.GCP_CLOUD_RUN_URL : (typeof GCP_CLOUD_RUN_URL !== 'undefined' ? GCP_CLOUD_RUN_URL : '');

  const gcp_weight = typeof env !== 'undefined' ? env.GCP_WEIGHT : (typeof GCP_WEIGHT !== 'undefined' ? GCP_WEIGHT : '50');

  const gcp_region = typeof env !== 'undefined' ? env.GCP_REGION : (typeof GCP_REGION !== 'undefined' ? GCP_REGION : 'us-central1');

  return [
    {
      name: 'gcp-cloud-run',
      url: gcp_url,
      health: gcp_url ? `${gcp_url}/health` : '',
      region: gcp_region,
      timeout: 5000,
      retries: 3,
      weight: parseInt(gcp_weight || '50', 10),
    }
  ].filter(b => b.url)
}

async function handleRequest(request) {
  const url = new URL(request.url)
  const backends = getBackends()

  if (backends.length === 0) {
    return new Response('No backends configured', { status: 503 })
  }

  // বাংলা মন্তব্য: P1 Fix — Cloudflare KV থেকে সার্কিট স্টেট রিড করা হচ্ছে রেস কন্ডিশন ও স্টেট ড্রিফট এড়াতে।
  const kv = getKV();
  let localState = { ...circuitBreakerState };
  if (kv) {
    try {
      const cached = await kv.get('SUPREMEAI_CIRCUIT_BREAKER_V2', { type: 'json' });
      if (cached) {
        localState = cached;
      }
    } catch (e) {
      console.error("KV read error for circuit breaker:", e);
    }
  }

  if (Date.now() < localState.brokenUntil) {
    // Circuit is open, return emergency response without hitting KV or origin
    console.error('Circuit Breaker is open. Returning emergency fallback response.');
    return new Response('Service temporarily unavailable. Please try again shortly.', { status: 503, headers: { 'Content-Type': 'text/plain' } });
  }

  const healthyBackends = await getHealthyBackendsFromKV(backends)
  // Architectural Fix #1: Add a fallback to all backends if none are healthy.
  if (healthyBackends.length === 0) {
    console.warn('All backends reported as unhealthy. Attempting to route to a backend as a last resort.');
    const backend = weightedPick(backends); // Fallback to all configured backends
    return forwardRequest(request, backend, url);
  }

  const backend = weightedPick(healthyBackends)
  const target = new URL(url.pathname + url.search, backend.url)

  try {
    const response = await fetch(target, {
      // Architectural Fix #2: Use a separate signal for retries within the worker.
      // This is a placeholder for a more complex retry logic if you were to implement it here.
      // For now, we just use the backend's timeout.
      method: request.method,
      headers: omitWranglerHeaders(request.headers),
      body: request.method !== 'GET' ? await request.text() : null,
      signal: AbortSignal.timeout(backend.timeout),
    })

    return new Response(response.body, {
      status: response.status,
      headers: omitHopByHopHeaders(new Headers(response.headers)),
    })
  } catch (err) {
    return new Response(`Backend ${backend.name} error: ${err.message}`, { status: 502 })
  }
}

async function forwardRequest(request, backend, originalUrl) {
  const target = new URL(originalUrl.pathname + originalUrl.search, backend.url);

  try {
    const response = await fetch(target, {
      method: request.method,
      headers: omitWranglerHeaders(request.headers),
      body: request.method !== 'GET' && request.method !== 'HEAD' ? await request.text() : null,
      signal: AbortSignal.timeout(backend.timeout),
    });

    return new Response(response.body, {
      status: response.status,
      headers: omitHopByHopHeaders(new Headers(response.headers)),
    });
  } catch (err) {
    return new Response(`Last-resort routing to backend ${backend.name} failed: ${err.message}`, { status: 502 });
  }
}

async function getHealthyBackendsFromKV(backends) {
  try {
    const kv = typeof SUPREMEAI_KV !== 'undefined' ? SUPREMEAI_KV : null;
    if (kv) {
      const cached = await kv.get('healthy_backends');
      if (cached) {
        const healthyNames = JSON.parse(cached);
        const filtered = backends.filter(b => healthyNames.includes(b.name));
        if (filtered.length > 0) {
          return filtered;
        }
      }
    }
  } catch (e) {
    console.error('KV read error:', e);
  }
  // Fallback to direct health check if KV is empty or fails
  const directlyChecked = await getHealthyBackends(backends);
  if (directlyChecked.length === 0 && backends.length > 0) {
    // All backends are unhealthy, trip the circuit breaker
    let localState = { ...circuitBreakerState };
    const kv = getKV();
    if (kv) {
      try {
        const cached = await kv.get('SUPREMEAI_CIRCUIT_BREAKER_V2', { type: 'json' });
        if (cached) {
          localState = cached;
        }
      } catch (e) {
        console.error("KV read error during state mutation:", e);
      }
    }
    localState.failureCount++;
    localState.lastFailureTime = Date.now();
    // If it fails 3 times in a row, open the circuit for 1 minute
    if (localState.failureCount >= 3) {
      console.error('All backends unhealthy after direct check. Tripping circuit breaker for 60 seconds.');
      localState.brokenUntil = Date.now() + 60000; // Open for 60 seconds
      localState.failureCount = 0; // Reset count
    }
    Object.assign(circuitBreakerState, localState);
    if (kv) {
      try {
        // বাংলা মন্তব্য: P1 Fix — অন্যান্য Isolates-এর সাথে ব্রেকার স্টেট সিঙ্ক করতে KV-তে লিখা হচ্ছে।
        await kv.put('SUPREMEAI_CIRCUIT_BREAKER_V2', JSON.stringify(localState), { expirationTtl: 300 });
      } catch (e) {
        console.error("KV write error during state mutation:", e);
      }
    }
  }
  return directlyChecked;
}

async function checkHealthAndStore() {
  const backends = getBackends()
  if (backends.length === 0) return

  const healthyBackends = await getHealthyBackends(backends)
  const healthyNames = healthyBackends.map(b => b.name)

  const kv = getKV();
  if (kv) {
    // আর্কিটেকচারাল ফিক্স #2: Add a TTL to prevent using stale data if the cron fails
    await kv.put('healthy_backends', JSON.stringify(healthyNames), {
      expirationTtl: 60 // Expire after 60 seconds
    });
    console.log('Saved healthy backends to KV:', healthyNames)
  }
}

async function getHealthyBackends(backends) {
  const results = await Promise.allSettled(
    backends.map(async backend => {
      for (let attempt = 0; attempt < backend.retries; attempt++) {
        try {
          const res = await fetch(backend.health, { signal: AbortSignal.timeout(backend.timeout) })
          if (res.ok) return backend
        } catch (_) {
          if (attempt === backend.retries - 1) return null
          await new Promise(r => setTimeout(r, 200 * (attempt + 1)))
        }
      }
      return null
    })
  )
  return results.filter(r => r.status === 'fulfilled' && r.value).map(r => r.value)
}

function weightedPick(backends) {
  const total = backends.reduce((sum, b) => sum + (b.weight || 0), 0)
  if (total === 0) return backends[Math.floor(Math.random() * backends.length)]
  let r = Math.random() * total
  for (const b of backends) {
    r -= b.weight || 0
    if (r <= 0) return b
  }
  return backends[backends.length - 1]
}

function omitWranglerHeaders(headers) {
  const allowlist = ['content-type', 'authorization', 'x-telegram-bot-token']
  const out = new Headers()
  headers.forEach((v, k) => { if (allowlist.includes(k.toLowerCase()) || !k.startsWith('cf-')) out.set(k, v) })
  return out
}

function omitHopByHopHeaders(headers) {
  const block = new Set(['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailer', 'transfer-encoding', 'upgrade'])
  const out = new Headers()
  headers.forEach((v, k) => { if (!block.has(k.toLowerCase())) out.set(k, v) })
  return out
}

```

### 📄 `infrastructure/deploy.ps1`

```ps1
<#
.SYNOPSIS
SupremeAI 2.0 deployment orchestrator for GCP Cloud Run, Railway, Render.
.PARAMETER Target
Optional deployment target: gcp | all (default: all)
#>
param(
  [ValidateSet('gcp', 'all')]
  [string]$Target = 'all'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"

function Log($Message) { Write-Host "[DEPLOY] $Message" -ForegroundColor Cyan }
function Fail($Message) { Write-Host "[DEPLOY][FAIL] $Message" -ForegroundColor Red; exit 1 }

function Test-Prerequisites {
  Log "Checking prerequisites..."
  $required = @('gcloud', 'docker', 'git')
  $missing = @()
  foreach ($cmd in $required) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { $missing += $cmd }
  }
  if ($missing) { Fail "Missing tools: $($missing -join ', ')" }
  if (Test-Path $EnvFile) {
    foreach ($line in Get-Content $EnvFile) {
      $trimmed = $line.Trim()
      if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
      $idx = $trimmed.IndexOf('=')
      if ($idx -lt 1) { continue }
      $k = $trimmed.Substring(0, $idx).Trim()
      $v = $trimmed.Substring($idx + 1).Trim()
      if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
        $v = $v.Substring(1, $v.Length - 2)
      }
      [System.Environment]::SetEnvironmentVariable($k, $v, 'Process')
    }
  }
}

function Get-RegistryImage {
  param([string]$ProjectId, [string]$Region)
  $artifactRepo = "$Region-docker.pkg.dev/$ProjectId/supremeai"
  $tag = if ($env:GITHUB_SHA) { $env:GITHUB_SHA } else { "local-$(Get-Date -Format 'yyyyMMdd-HHmmss')" }
  return "$artifactRepo/supremeai:$tag"
}

function Deploy-GCP {
  param([string]$EnvTarget)
  Log "Deploying to GCP Cloud Run... (target: $EnvTarget)"
  if (-not $env:GCP_PROJECT_ID) { Fail "GCP_PROJECT_ID is not set" }
  if (-not $env:GCP_REGION) { $env:GCP_REGION = 'us-central1' }
  if (-not $env:GCP_SERVICE_NAME) { $env:GCP_SERVICE_NAME = 'supremeai' }
  if ($EnvTarget -eq 'production') { $env:ENV = 'production' } else { $env:ENV = $EnvTarget }

  $image = Get-RegistryImage -ProjectId $env:GCP_PROJECT_ID -Region $env:GCP_REGION
  Log "Building and pushing $image"
  docker build -t $image (Join-Path $ProjectRoot '.')
  if ($LASTEXITCODE -ne 0) { Fail 'Docker build failed' }
  docker push $image
  if ($LASTEXITCODE -ne 0) { Fail 'Docker push failed' }

  # বাংলা মন্তব্য: P0 Fix — Secrets কে CLI arguments-এ embed করা নিষিদ্ধ।
  # পরিবর্তে --set-secrets flag ব্যবহার করে GCP Secret Manager reference দেওয়া হবে।
  $setEnvVars = @("ENV=$EnvTarget")
  if ($env:GCP_PROJECT_ID) { $setEnvVars += "GCP_PROJECT_ID=$env:GCP_PROJECT_ID" }
  if ($env:GCP_REGION) { $setEnvVars += "GCP_REGION=$env:GCP_REGION" }

  $setSecrets = @()
  if ($env:OPENAI_API_KEY) { $setSecrets += "OPENAI_API_KEY=projects/$env:GCP_PROJECT_ID/secrets/OPENAI_API_KEY:latest" }
  if ($env:TELEGRAM_BOT_TOKEN) { $setSecrets += "TELEGRAM_BOT_TOKEN=projects/$env:GCP_PROJECT_ID/secrets/TELEGRAM_BOT_TOKEN:latest" }
  if ($env:SUPABASE_URL) { $setEnvVars += "SUPABASE_URL=$env:SUPABASE_URL" }
  if ($env:SUPABASE_KEY) { $setSecrets += "SUPABASE_KEY=projects/$env:GCP_PROJECT_ID/secrets/SUPABASE_KEY:latest" }
  if ($env:UPSTASH_REDIS_REST_URL) { $setEnvVars += "UPSTASH_REDIS_REST_URL=$env:UPSTASH_REDIS_REST_URL" }
  if ($env:UPSTASH_REDIS_REST_TOKEN) { $setSecrets += "UPSTASH_REDIS_REST_TOKEN=projects/$env:GCP_PROJECT_ID/secrets/UPSTASH_REDIS_REST_TOKEN:latest" }

  $envValue = $setEnvVars -join ','
  $gcloudArgs = @(
    'run', 'deploy', $env:GCP_SERVICE_NAME,
    '--image', $image,
    '--region', $env:GCP_REGION,
    '--project', $env:GCP_PROJECT_ID,
    '--no-allow-unauthenticated',
    '--set-env-vars', $envValue
  )
  if ($setSecrets.Count -gt 0) {
    $gcloudArgs += '--set-secrets'
    $gcloudArgs += ($setSecrets -join ',')
  }
  if ($env:PORT) {
    $gcloudArgs += '--port'
    $gcloudArgs += $env:PORT
  }

  & gcloud @gcloudArgs
  if ($LASTEXITCODE -ne 0) { Fail "gcloud deploy failed" }

  & gcloud run services update-traffic $env:GCP_SERVICE_NAME --region $env:GCP_REGION --project $env:GCP_PROJECT_ID --to-latest
  if ($LASTEXITCODE -ne 0) { Fail "traffic promotion failed" }
  Log 'GCP Cloud Run deployment completed'
}



try {
  Test-Prerequisites
  if ($Target -eq 'all' -or $Target -eq 'gcp') { Deploy-GCP -EnvTarget production }
  Log 'Deployment orchestration completed.'
}
catch { Fail $_ }

```

### 📄 `infrastructure/docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  nats:
    image: nats:latest
    command: "-js -a super_secret_token"
    ports:
      - "4222:4222"
    networks:
      - supreme_net

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    networks:
      - supreme_net

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      - nats
      - redis
    environment:
      - NATS_URL=nats://super_secret_token@nats:4222
      - REDIS_URL=redis://redis:6379
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks:
      - supreme_net

  swarm-worker:
    build:
      context: ./backend
      dockerfile: docker/swarm-worker.Dockerfile
    deploy:
      replicas: 3
    depends_on:
      - nats
    environment:
      - NATS_URL=nats://super_secret_token@nats:4222
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks:
      - supreme_net

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
    networks:
      - supreme_net

networks:
  supreme_net:
    driver: bridge

```

### 📄 `infrastructure/docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    restart: always
    environment:
      - POSTGRES_USER=${POSTGRES_USER:?POSTGRES_USER must be set}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}
      - POSTGRES_DB=${POSTGRES_DB:?POSTGRES_DB must be set}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - supreme_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=db
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${POSTGRES_DB:?POSTGRES_DB must be set}
      - DB_POSTGRESDB_USER=${POSTGRES_USER:?POSTGRES_USER must be set}
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY:?N8N_ENCRYPTION_KEY must be set}
      - WEBHOOK_URL=http://${CLOUD_SERVER_IP:-127.0.0.1}:5678/
    depends_on:
      - db
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - supreme_network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://127.0.0.1:5678/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  supremeai_backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - N8N_INTERNAL_URL=http://n8n:5678
      - OLLAMA_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      n8n:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://127.0.0.1:8000/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 20s
    volumes:
      - ./backend/data:/app/data
      - ./backend/logs:/app/logs
    networks:
      - supreme_network

  neo4j:
    image: neo4j:5.12.0-community
    restart: always
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=${NEO4J_AUTH:-neo4j/password}
    volumes:
      - neo4j_data:/data
      - neo4j_import:/import
      - neo4j_plugins:/plugins
    networks:
      - supreme_network

networks:
  supreme_network:
    driver: bridge

volumes:
  postgres_data:
  n8n_data:
  neo4j_data:
  neo4j_import:
  neo4j_plugins:

```

### 📄 `infrastructure/render.admin.yaml`

```yaml
# render.admin.yaml — SupremeAI 2.0 Admin Instance Blueprint (Zero Cost Edition)
#
# বাংলা মন্তব্য: এই ব্লুপ্রিন্টটি আলাদা — মূল `render.yaml` (User instance) থেকে ইচ্ছাকৃতভাবে
# পৃথক রাখা হয়েছে, কারণ Render Blueprints (render.yaml) একটি রিপো-কে একটি নির্দিষ্ট Render
# অ্যাকাউন্টের সাথে সিঙ্ক করে — একই YAML দিয়ে দুইটি ভিন্ন ফ্রি-টিয়ার অ্যাকাউন্টে ডিপ্লয় করা যায় না।
#
# Setup (one-time, manual — Render Blueprints don't support multi-account targeting):
#   1. Log into your SECOND Render.com free-tier account.
#   2. New → Blueprint → point it at this same GitHub repo, but set the blueprint
#      file path to `infrastructure/render.admin.yaml` (Render lets you choose a
#      non-default blueprint path when creating the Blueprint instance).
#   3. Sync the same secrets used by the User instance (SUPABASE_*, REDIS_URL, etc.)
#      into THIS account's env var dashboard — they are intentionally not duplicated
#      in source. Additionally set the Admin-only secrets below (Discord/Resend/JWT).
#   4. Set ADMIN_HEALTH_URL as a GitHub Actions secret in the repo (see
#      .github/workflows/admin-keepalive.yml) to this service's /api/v1/health URL,
#      so the free-tier instance never cold-starts and breaks JIT OTP timing.
#
# This is purely additive — it does not touch or replace the existing render.yaml
# (User instance) in the repo root.

services:
  - type: web
    name: supremeai-admin
    env: image
    image:
      url: ghcr.io/paykaribazaronline/supremeai/supremeai-backend:latest
    region: singapore
    plan: free
    healthCheckPath: /api/v1/health
    autoDeploy: false
    envVars:
      - key: PORT
        value: 8080
      - key: ENV
        value: production
      # বাংলা মন্তব্য: এই একটি ফ্ল্যাগই core/app_admin.py লোড করায় (main.py) and
      # database/session.py-কে min=1/max=3 PgBouncer pool limit-এ পাঠায়।
      - key: SERVICE_ROLE
        value: admin
      # বাংলা মন্তব্য: Alert-only ডিফল্ট — false-positive rate যাচাই না হওয়া পর্যন্ত ব্লক করবে না।
      - key: ENFORCE_ANTI_HACKING
        value: false
      # বাকি সিক্রেটগুলো ড্যাশবোর্ড থেকে সিঙ্ক হবে (Upstash & Supabase — same DB/Redis as User instance)
      - key: REDIS_URL
        sync: false
      - key: UPSTASH_REDIS_REST_URL
        sync: false
      - key: UPSTASH_REDIS_REST_TOKEN
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: SUPABASE_DATABASE_URL_POOLER
        sync: false
      - key: SUPREMEAI_JWT_SECRET
        sync: false
      - key: SUPREMEAI_ADMIN_PASSWORD_HASH
        sync: false
      - key: SUPREMEAI_ENCRYPTION_KEY
        sync: false
      - key: SUPREMEAI_DOCS_PASSWORD
        sync: false
      - key: SUPREMEAI_API_TOKEN
        sync: false
      # Admin-only: JIT OTP delivery channels
      - key: DISCORD_OTP_WEBHOOK_URL
        sync: false
      - key: RESEND_API_KEY
        sync: false
      - key: ADMIN_NOTIFICATION_EMAIL
        sync: false
      - key: OTP_COOLDOWN_SECONDS
        value: 60
      # Admin API only ever trusts the Firebase-hosted console — never the Vercel user client.
      - key: ADMIN_CORS_ORIGINS
        value: '["https://supremeai-admin.web.app"]'
      - key: ALLOWED_HOSTS
        value: 'supremeai-admin.onrender.com'

```

### 📄 `infrastructure/vitest-report.json`

```json
{"numTotalTestSuites":2,"numPassedTestSuites":2,"numFailedTestSuites":0,"numPendingTestSuites":0,"numTotalTests":3,"numPassedTests":3,"numFailedTests":0,"numPendingTests":0,"numTodoTests":0,"snapshot":{"added":0,"failure":false,"filesAdded":0,"filesRemoved":0,"filesRemovedList":[],"filesUnmatched":0,"filesUpdated":0,"matched":0,"total":0,"unchecked":0,"uncheckedKeysByFile":[],"unmatched":0,"updated":0,"didUpdate":false},"startTime":1783140786443,"success":true,"testResults":[{"assertionResults":[{"ancestorTitles":["Cloudflare Worker Circuit Breaker E2E Test"],"fullName":"Cloudflare Worker Circuit Breaker E2E Test αª¼αºìαª»αª╛αªòαªÅαª¿αºìαªí αª╕αºüαª╕αºìαªÑ αªÑαª╛αªòαª▓αºç αª╕αª½αª▓αª¡αª╛αª¼αºç αª░αª┐αªòαºïαºƒαºçαª╕αºìαªƒ αª½αª░αªôαºƒαª╛αª░αºìαªí αªòαª░αª¼αºç","status":"passed","title":"αª¼αºìαª»αª╛αªòαªÅαª¿αºìαªí αª╕αºüαª╕αºìαªÑ αªÑαª╛αªòαª▓αºç αª╕αª½αª▓αª¡αª╛αª¼αºç αª░αª┐αªòαºïαºƒαºçαª╕αºìαªƒ αª½αª░αªôαºƒαª╛αª░αºìαªí αªòαª░αª¼αºç","duration":154.7548999999999,"failureMessages":[],"meta":{}},{"ancestorTitles":["Cloudflare Worker Circuit Breaker E2E Test"],"fullName":"Cloudflare Worker Circuit Breaker E2E Test αªƒαª╛αª¿αª╛ αº⌐ αª¼αª╛αª░ αª╣αºçαª▓αªÑ αªÜαºçαªò αª½αºçαªçαª▓ αª╣αª▓αºç αª╕αª╛αª░αºìαªòαª┐αªƒ αª¼αºìαª░αºçαªòαª╛αª░ αªƒαºìαª░αª┐αª¬ αªòαª░αª¼αºç αªÅαª¼αªé 503 αª░αºçαª╕αª¬αª¿αºìαª╕ αªªαºçαª¼αºç","status":"passed","title":"αªƒαª╛αª¿αª╛ αº⌐ αª¼αª╛αª░ αª╣αºçαª▓αªÑ αªÜαºçαªò αª½αºçαªçαª▓ αª╣αª▓αºç αª╕αª╛αª░αºìαªòαª┐αªƒ αª¼αºìαª░αºçαªòαª╛αª░ αªƒαºìαª░αª┐αª¬ αªòαª░αª¼αºç αªÅαª¼αªé 503 αª░αºçαª╕αª¬αª¿αºìαª╕ αªªαºçαª¼αºç","duration":83.92869999999994,"failureMessages":[],"meta":{}},{"ancestorTitles":["Cloudflare Worker Circuit Breaker E2E Test"],"fullName":"Cloudflare Worker Circuit Breaker E2E Test αª╕αª╛αª░αºìαªòαª┐αªƒ αª¼αºìαª░αºçαªòαª╛αª░ αªƒαºìαª░αª┐αª¬ αªòαª░αª╛αª░ αª¬αª░αªô αªÅαªòαª╛αªºαª┐αªò αª░αª┐αªòαºïαºƒαºçαª╕αºìαªƒαºç αª¿αª┐αª░αª╛αª¬αªª 503 αª½αºçαª░αªñ αªªαºçαª¼αºç","status":"passed","title":"αª╕αª╛αª░αºìαªòαª┐αªƒ αª¼αºìαª░αºçαªòαª╛αª░ αªƒαºìαª░αª┐αª¬ αªòαª░αª╛αª░ αª¬αª░αªô αªÅαªòαª╛αªºαª┐αªò αª░αª┐αªòαºïαºƒαºçαª╕αºìαªƒαºç αª¿αª┐αª░αª╛αª¬αªª 503 αª½αºçαª░αªñ αªªαºçαª¼αºç","duration":48.45399999999995,"failureMessages":[],"meta":{}}],"startTime":1783140789489,"endTime":1783140789776.454,"status":"passed","message":"","name":"C:/Users/n/supremeai/supremeai_2.0/scripts/cloudflare_worker.test.js"}]}

```

### 📄 `infrastructure/cloudflare/enhanced-worker.js`

```js
// infrastructure/cloudflare/enhanced-worker.js
// Enhanced Cloudflare Worker for SupremeAI 2.0 Edge Computing

/**
 * Enhanced Cloudflare Worker implementing:
 * 1. Multi-layer edge caching
 * 2. Request/response transformation
 * 3. Rate limiting at edge
 * 4. Geographic routing
 * 5. Request deduplication
 */

// Configuration
const CONFIG = {
  // Cache TTL values (in seconds)
  CACHE_TTL: {
    STATIC_ASSETS: 31536000,   // 1 year
    API_RESPONSES: 300,        // 5 minutes
    AI_RESPONSES: 60,          // 1 minute
    RATE_LIMIT_WINDOW: 60,     // 1 minute
  },

  // Rate limiting (requests per window)
  RATE_LIMIT: {
    DEFAULT: 100,              // 100 requests per minute per IP
    AUTHENTICATED: 1000,       // 1000 requests per minute for authenticated users
  },

  // Cache keys prefixes
  CACHE_PREFIXES: {
    API: "supremeai:api:",
    AI: "supremeai:ai:",
    RATE_LIMIT: "supremeai:ratelimit:",
    DEDUP: "supremeai:dedup:",
  }
};

/**
 * Main fetch handler
 */
export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url);
      const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
      const country = request.headers.get('CF-IPCountry') || 'unknown';

      // Log request for analytics (sampling to avoid overload)
      if (Math.random() < 0.1) { // 10% sampling
        console.log(`[EDGE] ${request.method} ${url.pathname} from ${ip} (${country})`);
      }

      // Route to appropriate handler based on path
      if (url.pathname.startsWith('/api/')) {
        return await handleApiRequest(request, env, ctx);
      } else if (url.pathname.startsWith('/ai/')) {
        return await handleAiRequest(request, env, ctx);
      } else if (url.pathname.startsWith('/cdn/')) {
        return await handleStaticAssets(request, env, ctx);
      } else if (url.pathname.startsWith('/health')) {
        return await handleHealthCheck(request, env, ctx);
      } else {
        // Default: proxy to proxy to origin
        return await fetch(request);
      }
    } catch (error) {
      console.error('[EDGE] Error in worker:', error);
      return new Response('Internal Server Error', {
        status: 500,
        headers: { 'Content-Type': 'text/plain' }
      });
    }
  }
};

/**
 * Handle API requests with caching and rate limiting
 */
async function handleApiRequest(request, env, ctx) {
  const url = new URL(request.url);

  // Skip caching for non-GET requests
  if (request.method !== 'GET') {
    return await proxyToOrigin(request, env);
  }

  // Check rate limit
  const rateLimitResult = await checkRateLimit(
    request,
    env,
    `${CONFIG.CACHE_PREFIXES.RATE_LIMIT}api:`,
    CONFIG.RATE_LIMIT.DEFAULT
  );

  if (!rateLimitResult.allowed) {
    return new Response('Rate limit exceeded', {
      status: 429,
      headers: {
        'Content-Type': 'text/plain',
        'Retry-After': String(rateLimitResult.resetIn)
      }
    });
  }

  // Generate cache key
  const cacheKey = `${CONFIG.CACHE_PREFIXES.API}${crypto.SHA256(request.url)}`;

  // Try to get from cache
  const cachedResponse = await caches.default.match(
    new Request(`https://cache.cloudflare.com/${cacheKey}`),
    { cacheName: 'api-cache' }
  );

  if (cachedResponse) {
    // Add cache hit header
    const newHeaders = new Headers(cachedResponse.headers);
    newHeaders.set('X-Cache-Status', 'HIT');
    newHeaders.set('X-Cache-Layer', 'EDGE');

    return new Response(cachedResponse.body, {
      status: cachedResponse.status,
      headers: newHeaders
    });
  }

  // Fetch from origin
  const originResponse = await proxyToOrigin(request, env);

  // Cache successful responses
  if (originResponse.ok) {
    const responseToCache = new Response(originResponse.body, originResponse);
    responseToCache.headers.set('X-Cache-Status', 'MISS');
    responseToCache.headers.set('X-Cache-Layer', 'ORIGIN');

    ctx.waitUntil(
      caches.default.putToCache(
        cacheKey,
        responseToCache,
        env,
        CONFIG.CACHE_TTL.API_RESPONSES
      )
    );
  }

  return originResponse;
}

/**
 * Handle AI requests with specialized caching and deduplication
 */
async function handleAiRequest(request, env, ctx) {
  // Only cache POST requests with cacheable content-type
  if (request.method !== 'POST') {
    return await proxyToOrigin(request, env);
  }

  // Check rate limit (stricter for AI endpoints)
  const rateLimitResult = await checkRateLimit(
    request,
    env,
    `${CONFIG.CACHE_PREFIXES.RATE_LIMIT}ai:`,
    Math.floor(CONFIG.RATE_LIMIT.DEFAULT / 2) // Half the rate limit for AI
  );

  if (!rateLimitResult.allowed) {
    return new Response('AI service rate limit exceeded', {
      status: 429,
      headers: {
        'Content-Type': 'text/plain',
        'Retry-After': String(rateLimitResult.resetIn)
      }
    });
  }

  // Get request body for cache key generation
  let requestBody = '';
  try {
    const clone = request.clone();
    requestBody = await clone.text();
  } catch (e) {
    // If we can't read the body, fall back to URL-only caching
    requestBody = '';
  }

  // Create cache key from method, URL, and body hash
  const bodyHash = requestBody ? await crypto.SHA256(requestBody) : 'no-body';
  const cacheKey = `${CONFIG.CACHE_PREFIXES.AI}${crypto.SHA256(`${request.method}:${request.url}:${bodyHash}`)}`;

  // Check for duplicate requests (deduplication)
  const dedupKey = `${CONFIG.CACHE_PREFIXES.DEDUP}${cacheKey}`;
  const isDuplicate = await checkAndSetDuplicate(env, dedupKey, 5); // 5 second dedup window

  if (isDuplicate) {
    // Return cached response if available
    const cachedResponse = await caches.default.match(
      new Request(`https://cache.cloudflare.com/${cacheKey}`),
      { cacheName: 'ai-cache' }
    );

    if (cachedResponse) {
      const newHeaders = new Headers(cachedResponse.headers);
      newHeaders.set('X-Cache-Status', 'HIT');
      newHeaders.set('X-Deduplicated', 'true');

      return new Response(cachedResponse.body, {
        status: cachedResponse.status,
        headers: newHeaders
      });
    }

    // If no cached response, ask client to retry shortly
    return new Response('Please wait...', {
      status: 202,
      headers: {
        'Content-Type': 'text/plain',
        'Retry-After': '2'
      }
    });
  }

  // Try to get from cache
  const cachedResponse = await caches.default.match(
    new Request(`https://cache.cloudflare.com/${cacheKey}`),
    { cacheName: 'ai-cache' }
  );

  if (cachedResponse) {
    const newHeaders = new Headers(cachedResponse.headers);
    newHeaders.set('X-Cache-Status', 'HIT');
    newHeaders.set('X-Cache-Layer', 'EDGE');
    newHeaders.set('X-Deduplicated', 'false');

    return new Response(cachedResponse.body, {
      status: cachedResponse.status,
      headers: newHeaders
    });
  }

  // Fetch from origin
  const originResponse = await proxyToOrigin(request, env);

  // Cache successful AI responses (shorter TTL)
  if (originResponse.ok) {
    const responseToCache = new Response(originResponse.body, originResponse);
    responseToCache.headers.set('X-Cache-Status', 'MISS');
    responseToCache.headers.set('X-Cache-Layer', 'ORIGIN');
    responseToCache.headers.set('X-Deduplicated', 'false');

    ctx.waitUntil(
      caches.default.put(
        new Request(`https://cache.cloudflare.com/${cacheKey}`),
        responseToCache.clone(),
        { cacheName: 'ai-cache' }
      )
    );

    // Set expiration
    ctx.waitUntil(
      setCacheExpiration(
        `https://cache.cloudflare.com/${cacheKey}`,
        env,
        CONFIG.CACHE_TTL.AI_RESPONSES
      )
    );
  }

  return originResponse;
}

/**
 * Handle static assets with aggressive caching
 */
async function handleStaticAssets(request, env, ctx) {
  // Only cache GET requests for static assets
  if (request.method !== 'GET') {
    return await fetch(request);
  }

  const url = new URL(request.url);
  const cacheKey = `${CONFIG.CACHE_PREFIXES.API}${url.pathname}`;

  // Try cache first
  const cachedResponse = await caches.default.match(
    new Request(`https://cache.cloudflare.com/${cacheKey}`),
    { cacheName: 'static-assets' }
  );

  if (cachedResponse) {
    const newHeaders = new Headers(cachedResponse.headers);
    newHeaders.set('X-Cache-Status', 'HIT');
    newHeaders.set('X-Asset-Type', 'STATIC');

    return new Response(cachedResponse.body, {
      status: cachedResponse.status,
      headers: newHeaders
    });
  }

  // Fetch from origin (R2 bucket or origin server)
  const originResponse = await fetch(request);

  // Cache static assets aggressively
  if (originResponse.ok) {
    const responseToCache = new Response(originResponse.body, originResponse);
    responseToCache.headers.set('X-Cache-Status', 'MISS');
    responseToCache.headers.set('X-Asset-Type', 'STATIC');

    ctx.waitUntil(
      caches.default.put(
        new Request(`https://cache.cloudflare.com/${cacheKey}`),
        responseToCache.clone(),
        { cacheName: 'static-assets' }
      )
    );

    // Very long TTL for static assets
    ctx.waitUntil(
      setCacheExpiration(
        `https://cache.cloudflare.com/${cacheKey}`,
        env,
        CONFIG.CACHE_TTL.STATIC_ASSETS
      )
    );
  }

  return originResponse;
}

/**
 * Health check endpoint
 */
async function handleHealthCheck(request, env, ctx) {
  return new Response(JSON.stringify({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'SupremeAI 2.0 Edge Worker',
    version: '2.0.0'
  }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * Proxy request to origin server
 */
async function proxyToOrigin(request, env) {
  // In a real implementation, this would forward to your origin
  // For now, we'll simulate or use a default backend
  const originUrl = env.ORIGIN_URL || 'https://your-origin-server.com';

  const url = new URL(request.url);
  const originUrlObj = new URL(url.pathname + url.search, originUrl);

  const originRequest = new Request(originUrlObj.toString(), {
    method: request.method,
    headers: request.headers,
    body: request.body,
    redirect: 'follow'
  });

  return fetch(originRequest);
}

/**
 * Check rate limit for an identifier using atomic Native Rate Limiting
 */
async function checkRateLimit(request, env, prefix, limit) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';

  if (env.API_RATE_LIMITER) {
    const { success } = await env.API_RATE_LIMITER.limit({ key: `${prefix}${ip}` });
    return {
      allowed: success,
      resetIn: 60 // Fixed period based on the binding configuration
    };
  }

  // Graceful fallback if binding is not configured
  return { allowed: true, resetIn: 60 };
}

/**
 * Check and set duplicate request marker
 */
async function checkAndSetDuplicate(env, key, ttlSeconds) {
  const exists = await env.DUPLICATE_DB.get(key);

  if (exists) {
    return true; // Duplicate detected
  }

  // Set the deduplication key
  await env.DUPLICATE_DB.put(key, '1', {
    expiration: Math.floor(Date.now() / 1000) + ttlSeconds
  });

  return false; // Not a duplicate
}

/**
 * Helper to put response in cache with expiration
 */
async function putInCache(request, response, options = {}) {
  const cache = await caches.open(options.cacheName || 'default');
  return await cache.put(request, response);
}

/**
 * Helper to set cache expiration using cache tags or custom metadata
 */
async function setCacheExpiration(cacheKey, env, ttlSeconds) {
  // In Cloudflare Workers, we can't directly set TTL on cache objects
  // Instead, we rely on cache-control headers or use KV for metadata
  // This is a simplified implementation

  try {
    // Store expiration timestamp in KV
    const expiryTime = Math.floor(Date.now() / 1000) + ttlSeconds;
    await env.CACHE_METADATA.put(
      `exp:${cacheKey}`,
      String(expiryTime),
      { expiration: ttlSeconds }
    );
  } catch (e) {
    console.warn('Failed to set cache expiration metadata:', e);
  }
}

/**
 * SHA256 hash utility
 */
async function crypto.SHA256(message) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

```

### 📄 `infrastructure/cloudflare/worker.js`

```js
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Static Asset CDN from R2 bucket
    if (url.pathname.startsWith('/cdn/')) {
      const cacheKey = new Request(url.toString(), request);
      const cache = caches.default;

      let response = await cache.match(cacheKey);
      if (!response) {
        // Fetch from R2 bucket (assumed binding named STATIC_ASSETS)
        const objectName = url.pathname.replace('/cdn/', '');
        const object = await env.STATIC_ASSETS.get(objectName);

        if (object === null) {
          return new Response('Not Found', { status: 404 });
        }

        const headers = new Headers();
        object.writeHttpMetadata(headers);
        headers.set('etag', object.httpEtag);
        headers.set('Cache-Control', 'public, max-age=31536000'); // 1 year cache

        response = new Response(object.body, { headers });
        ctx.waitUntil(cache.put(cacheKey, response.clone()));
      }
      return response;
    }

    // Cache specific public API responses (e.g. repo list)
    if (request.method === 'GET' && url.pathname.startsWith('/api/repos')) {
      const cache = caches.default;
      let response = await cache.match(request);

      if (!response) {
        response = await fetch(request);
        if (response.ok) {
          response = new Response(response.body, response);
          response.headers.set('Cache-Control', 'public, max-age=300'); // 5 mins
          ctx.waitUntil(cache.put(request, response.clone()));
        }
      }
      return response;
    }

    // Default: pass through to origin
    return fetch(request);
  },
};

```

### 📄 `infrastructure/cloudflare/wrangler.toml`

```toml
name = "supremeai-edge"
main = "worker.js"
compatibility_date = "2026-06-17"

[vars]
GCP_CLOUD_RUN_URL = ""
RAILWAY_URL = ""
RENDER_URL = ""

[[unsafe.bindings]]
name = "API_RATE_LIMITER"
type = "ratelimit"
namespace_id = "1001"
simple = { limit = 100, period = 60 }

```

### 📄 `infrastructure/cloudrun/autoscale.yaml`

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: supremeai-backend
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/launch-stage: BETA
spec:
  template:
    metadata:
      annotations:
        # Autoscale bounds
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"

        # CPU allocation: CPU is always allocated so background tasks (agents) can run
        run.googleapis.com/cpu-throttling: "false"

        # Concurrency
        autoscaling.knative.dev/target: "80"
    spec:
      containerConcurrency: 80
      containers:
      - image: gcr.io/supremeai/backend:latest
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
        env:
        - name: GCP_PROJECT_ID
          value: "supremeai-a"
        - name: ENV
          value: "production"
        ports:
        - name: http1
          containerPort: 8000

```

### 📄 `infrastructure/cloudrun/multi_region.yaml`

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: supremeai-backend
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/launch-stage: BETA
spec:
  template:
    metadata:
      annotations:
        # Autoscale bounds
        autoscaling.knative.dev/minScale: "2"
        autoscaling.knative.dev/maxScale: "100"
        # CPU allocation: CPU is always allocated so background tasks (agents) can run
        run.googleapis.com/cpu-throttling: "false"
        # Concurrency
        autoscaling.knative.dev/target: "80"
        # Multi-region deployment via Cloud Run traffic split
        # Run `gcloud run services update-traffic` to route 80% -> us-central1, 20% -> europe-west1
        run.googleapis.com/location: "us-central1"
    spec:
      containerConcurrency: 80
      containers:
      - image: gcr.io/supremeai/backend:latest
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
        env:
        - name: GCP_PROJECT_ID
          value: "supremeai-a"
        - name: ENV
          value: "production"
        - name: GCP_REGION
          value: "us-central1"
        ports:
        - name: http1
          containerPort: 8000
---
# Secondary region: europe-west1 (deploy separately and use traffic-split)
# gcloud run services update supremeai-backend-europe \
#   --image=gcr.io/supremeai/backend:latest \
#   --region=europe-west1 \
#   --set-env-vars=ENV=production,GCP_REGION=europe-west1

```

### 📄 `infrastructure/firebase_functions/ocrTrigger.ts`

```ts
# SupremeAI — Firebase OCR Trigger
Provides a sample Cloud Function (Realtime Database + Firestore) that initiates an OCR task when a document is queued.
Use this as a reference; integrate into your actual functions source.

### Realtime Database reference implementation
- Database path: `/ocr-queue/{pushId}`
- Expected fields: `{ file_path: string, mime: string }`
- Result: writes `{ status: 'completed', result: any }` under `/ocr-results/{pushId}`

```

### 📄 `infrastructure/monitoring/docker-compose.monitoring.yml`

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

```

### 📄 `infrastructure/monitoring/grafana_dashboard.json`

```json
{
  "dashboard": {
    "title": "SupremeAI Metrics",
    "panels": [
      { "type": "graph", "title": "API Spend" },
      { "type": "graph", "title": "Model Distribution" },
      { "type": "graph", "title": "Error Rates" },
      { "type": "graph", "title": "Latency" }
    ]
  }
}

```

### 📄 `cloudflare-worker/wrangler.toml`

```toml
name = "supremeai-load-balance"
main = "src/index.js"
compatibility_date = "2025-01-01"

[triggers]
# প্রতি ১০ মিনিটে একাধিক সার্ভিস পিং করার শিডিউল
crons = ["*/10 * * * *"]

[vars]
PRIMARY_URL = "https://supremeai-backend.onrender.com"
ADMIN_URL = "https://supremeai-admin.onrender.com"
BACKUP_URL = "https://supremeai-studio-client.onrender.com"
BACKUP_HEALTH = "https://supremeai-studio-client-qb34.onrender.com/api/v1/health"

```

### 📄 `cloudflare-worker/src/index.js`

```js
export default {
  // ==========================================
  // কাজ ১: Load Balancer + Health Dashboard
  // ==========================================
  async fetch(request, env, ctx) {
    const services = {
      primary: env.PRIMARY_URL || "https://supremeai-backend.onrender.com",
      admin: env.ADMIN_URL || "https://supremeai-admin.onrender.com",
      backup: env.BACKUP_URL || "https://supremeai-studio-client.onrender.com",
    };

    const results = await Promise.allSettled(
      Object.entries(services).map(async ([name, url]) => {
        const alive = await this.pingWithRetry(url, 2);
        return { name, url, alive };
      })
    );

    const statuses = results.map(r =>
      r.status === "fulfilled" ? r.value : { alive: false, error: r.reason?.message }
    );
    const allAlive = statuses.every(s => s.alive);

    return new Response(JSON.stringify({
      status: allAlive ? "UP" : "DEGRADED",
      timestamp: new Date().toISOString(),
      services: statuses,
    }), {
      status: allAlive ? 200 : 503,
      headers: { "Content-Type": "application/json" },
    });
  },

  // ==========================================
  // কাজ ২: Keep-Alive Ping (প্রতি ১০ মিনিটে একাধিক সার্ভিস)
  // ==========================================
  async scheduled(event, env, ctx) {
    const targets = [
      env.PRIMARY_URL || "https://supremeai-backend.onrender.com/health",
      env.ADMIN_URL || "https://supremeai-admin.onrender.com/health",
      env.BACKUP_HEALTH || "https://supremeai-studio-client-qb34.onrender.com/api/v1/health",
    ];

    const results = await Promise.allSettled(
      targets.map(url => this.pingWithRetry(url, 3))
    );

    const alive = results.filter(r => r.status === "fulfilled" && r.value).length;
    console.log(`✅ KeepAlive: ${alive}/${targets.length} services alive at ${new Date().toISOString()}`);
  },

  // ==========================================
  // Helper: Retry logic with exponential backoff
  // ==========================================
  async pingWithRetry(url, maxRetries = 2) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(url, {
          headers: { "User-Agent": "Cloudflare-KeepAlive-Worker/2.0" },
          signal: AbortSignal.timeout(10000),
        });
        if (response.ok) return true;
        console.warn(`⚠️ Ping ${url} returned ${response.status}, retry ${i + 1}/${maxRetries}`);
      } catch (error) {
        console.error(`❌ Ping ${url} failed: ${error.message}, retry ${i + 1}/${maxRetries}`);
      }
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, 1000 * (i + 1)));
      }
    }
    return false;
  },
};

```

### 📄 `Dockerfile`

```txt
# Stage 1: Builder
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

# Cache layer: install only main dependencies (tools group excluded to save space on Render free tier)
COPY backend/pyproject.toml backend/poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --no-root --only main


# Stage 2: Runner
FROM python:3.11-slim AS runner
WORKDIR /app
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

# Create non-root user appuser
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only virtual environment (not full source code)
COPY --from=builder /app/.venv /app/.venv
COPY backend/ .
# Copy root-level 'skills' directory for core/evolution/auto_skill_creator.py imports
COPY skills/ ./skills/
# Copy ask_scribe.py for api/routes/knowledge.py imports
COPY ask_scribe.py ./

RUN chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
# EXPOSE port consistent with CMD's ${PORT:-8080} default
EXPOSE 8080

# Container health check — ensures Render/Cloud Run detects healthy state
# start-period 40s allows time for Python env to load on first boot
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Use main.py entrypoint for role-based boot, signal handling, and UVICORN_WORKERS support
# Note: Previously GUNICORN_WORKERS=4 default caused OOM on Render free tier (512MB RAM)
CMD ["sh", "-c", "python main.py"]

```

### 📄 `render.yaml`

```yaml
# render.yaml - SupremeAI 2.0 Master Blueprint (Zero Cost Edition)
services:
  # 1. Backend (GHCR Image - Zero Render Build Minutes)
  - type: web
    name: supremeai-backend
    env: image
    image:
      url: ghcr.io/paykaribazaronline/supremeai/supremeai-backend:latest
    region: singapore
    plan: free
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: PORT
        value: 8080
      - key: ENV
        value: production
      # বাকি সিক্রেটগুলো ড্যাশবোর্ড থেকে সিঙ্ক হবে (Upstash & Supabase)
      - key: REDIS_URL
        sync: false
      - key: UPSTASH_REDIS_REST_URL
        sync: false
      - key: UPSTASH_REDIS_REST_TOKEN
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: SUPABASE_DATABASE_URL_POOLER
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: SUPREMEAI_JWT_SECRET
        sync: false
      - key: SUPREMEAI_ADMIN_PASSWORD_HASH
        sync: false
      - key: SUPREMEAI_ENCRYPTION_KEY
        sync: false
      - key: SUPREMEAI_DOCS_PASSWORD
        sync: false
      - key: SUPREMEAI_API_TOKEN
        sync: false
      - key: STRIPE_API_KEY
        sync: false
      - key: STRIPE_WEBHOOK_SECRET
        sync: false
      - key: CI_WEBHOOK_SECRET
        sync: false
      - key: INFISICAL_TOKEN
        sync: false
      - key: INFISICAL_CLIENT_SECRET
        sync: false
      - key: CORS_ORIGINS
        value: '["https://supremeai-studio-client.onrender.com", "https://supremeai-studio-client-qb34.onrender.com", "https://tiny-stroopwafel-2d981c.netlify.app", "https://supremeai-lac.vercel.app", "https://supremeai-studio.vercel.app", "https://supremeai-a.web.app", "https://supremeai-admin.web.app"]'
      # বাংলা মন্তব্য: core/app_user.py এই User-role instance-এ CORS_ORIGINS নয়, USER_CORS_ORIGINS
      # পড়ে এবং production-এ খালি থাকলে বুট-টাইমে crash করে (Fail-Fast) — তাই আলাদাভাবে সেট করা হলো,
      # যাতে User API কঠোরভাবে শুধু Vercel/Netlify/Render client-গুলোকেই ট্রাস্ট করে (Admin console নয়)।
      - key: USER_CORS_ORIGINS
        value: '["https://supremeai-studio-client.onrender.com", "https://supremeai-studio-client-qb34.onrender.com", "https://tiny-stroopwafel-2d981c.netlify.app", "https://supremeai-lac.vercel.app", "https://supremeai-studio.vercel.app"]'
      - key: SERVICE_ROLE
        value: user
      - key: ALLOWED_HOSTS
        value: 'supremeai-backend.onrender.com,supremeai-backend-65hl.onrender.com'

  # 1.5. Admin Backend (Isolated Render instance — core/app_admin.py)
  # Note: Previously missing from render.yaml, now deployed as separate service for true isolation.
  # Separate domains/secrets mean user instance crash does not affect admin panel and vice versa.
  - type: web
    name: supremeai-admin
    env: image
    image:
      url: ghcr.io/paykaribazaronline/supremeai/supremeai-backend:latest
    region: singapore
    plan: free
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: PORT
        value: 8080
      - key: ENV
        value: production
      - key: REDIS_URL
        sync: false
      - key: UPSTASH_REDIS_REST_URL
        sync: false
      - key: UPSTASH_REDIS_REST_TOKEN
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: SUPABASE_DATABASE_URL_POOLER
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: SUPREMEAI_JWT_SECRET
        sync: false
      - key: SUPREMEAI_ADMIN_PASSWORD_HASH
        sync: false
      - key: SUPREMEAI_ENCRYPTION_KEY
        sync: false
      - key: SUPREMEAI_DOCS_PASSWORD
        sync: false
      - key: SUPREMEAI_API_TOKEN
        sync: false
      - key: DISCORD_OTP_WEBHOOK_URL
        sync: false
      - key: RESEND_API_KEY
        sync: false
      - key: ADMIN_NOTIFICATION_EMAIL
        sync: false
      - key: INFISICAL_TOKEN
        sync: false
      - key: INFISICAL_CLIENT_SECRET
        sync: false
      # বাংলা মন্তব্য: শুধমাত্র অ্যাডমিন কনসোল origin — Vercel/Netlify user client নয়
      - key: ADMIN_CORS_ORIGINS
        value: '["https://supremeai-admin.web.app"]'
      - key: SERVICE_ROLE
        value: admin
      # বাংলা মন্তব্ত: অ্যাডমিন সার্ভিসের জন্য প্রয়োজনীয় মিনিমাম রুট চেক ৫ সেট করা হলো
      - key: MIN_EXPECTED_ROUTES
        value: 5
      - key: ALLOWED_HOSTS
        value: 'supremeai-admin.onrender.com'

  # 2. Background Worker (Maintenance Pipeline, Sentinel, AutoHealer)
  # Runs cron-like background tasks without serving HTTP.
  # The web service also starts these in lifespan, but this worker provides
  # redundancy — if the web service restarts, the worker keeps monitoring.
  - type: worker
    name: supremeai-background-worker
    env: image
    image:
      url: ghcr.io/paykaribazaronline/supremeai/supremeai-backend:latest
    region: singapore
    plan: free
    autoDeploy: true
    startCommand: "python -c \"import asyncio; from core.maintenance_pipeline import maintenance_pipeline; maintenance_pipeline.start_monitoring(); from core.agent_supervisor import agent_supervisor; from core.sentinel_agent import sentinel; asyncio.run(agent_supervisor.start_agent('sentinel', lambda: sentinel.run_periodic_loop(), health_check_interval=60, max_restarts=10, restart_delay=1.0)); asyncio.run(agent_supervisor.start_monitor(check_interval=30)); asyncio.get_event_loop().run_forever()\""
    envVars:
      - key: ENV
        value: production
      - key: SERVICE_ROLE
        value: user
      - key: REDIS_URL
        sync: false
      - key: SUPABASE_DATABASE_URL_POOLER
        sync: false
      - key: SUPREMEAI_JWT_SECRET
        sync: false
      - key: INFISICAL_TOKEN
        sync: false
      - key: INFISICAL_CLIENT_SECRET
        sync: false
      - key: ALLOWED_HOSTS
        value: 'supremeai-backend.onrender.com'

  # 3. Frontend (Render Free Static Hosting)
  # Build command and env vars explicitly set for correct backend URL.
  - type: web
    name: supremeai-studio-client
    env: static
    buildCommand: "cd apps/studio-client && pnpm install && pnpm run build:user"
    staticPublishPath: "./apps/studio-client/dist-user"
    autoDeploy: true
    envVars:
      - key: VITE_API_URL
        value: https://supremeai-backend.onrender.com
      - key: VITE_API_BASE
        value: https://supremeai-backend.onrender.com
    routes:
      - type: rewrite
        source: /*
        destination: /index.html

```

### 📄 `vercel.json`

```json
{
  "version": 2,
  "buildCommand": "pnpm --filter supremeai-studio-client build:user",
  "ignoreCommand": "git diff --quiet HEAD^ HEAD ./apps/studio-client",
  "outputDirectory": "apps/studio-client/dist-user",
  "framework": "vite",
  "env": {
    "VITE_PORTAL_TYPE": "user"
  },
  "rewrites": [
    {
      "source": "/api/config/public",
      "destination": "https://supremeai-backend.onrender.com/api/config/public"
    },
    {
      "source": "/api/task/stream",
      "destination": "https://supremeai-backend.onrender.com/api/task/stream"
    },
    {
      "source": "/api/preferences/:userId/stream",
      "destination": "https://supremeai-backend.onrender.com/api/preferences/:userId/stream"
    },
    {
      "source": "/api/:path*",
      "destination": "https://supremeai-backend.onrender.com/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "https://supremeai-studio-client.onrender.com"
        },
        {
          "key": "Access-Control-Allow-Methods",
          "value": "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        },
        {
          "key": "Access-Control-Allow-Headers",
          "value": "Authorization, Content-Type, X-Request-ID, X-API-Key"
        }
      ]
    }
  ]
}

```


---

## 4. 🐛 Identified Vulnerabilities & Edge Cases

*Run external AI prompt against Section 3 above to populate.*

---

## 5. 🛠️ Recommended Delta Patches & Actions

*Pending audit execution.*

---
*Generated automatically by SupremeAI 2.0 Audit Generator Script.*
