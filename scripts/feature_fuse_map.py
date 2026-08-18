#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# বাংলা মন্তব্য: প্রতিটি এনভায়রনমেন্ট ভেরিয়েবল কোন ফিচারকে কন্ট্রোল করে তার ম্যাপ। 
# কোনো key মিসিং হলে কোন ফিচার বন্ধ হয়ে যাবে, তা ট্র্যাক করা হয়।
FUSE_MAP = {
    "SUPABASE_URL": {"feature": "Global Database & ai_memory", "severity": "CRITICAL", "fallback": "SQLite (Local Only)"},
    "SUPABASE_KEY": {"feature": "Global Database Access", "severity": "CRITICAL", "fallback": "None"},
    "REDIS_URL": {"feature": "Rate Limiting & Memory Cache", "severity": "HIGH", "fallback": "In-Memory (Single Node)"},
    "OPENAI_API_KEY": {"feature": "Advanced AI Reasoning", "severity": "HIGH", "fallback": "Local Ollama"},
    "ANTHROPIC_API_KEY": {"feature": "Claude Sonnet (Primary Engine)", "severity": "HIGH", "fallback": "Local Ollama"},
    "GITHUB_TOKEN": {"feature": "CI/CD & GitHub Integrations", "severity": "MEDIUM", "fallback": "None"},
    "RENDER_API_KEY": {"feature": "Auto Deployments", "severity": "HIGH", "fallback": "Manual Deploy"},
    "JWT_SECRET_KEY": {"feature": "User Authentication", "severity": "CRITICAL", "fallback": "None"},
    "STRIPE_SECRET_KEY": {"feature": "Billing & Subscription", "severity": "HIGH", "fallback": "None"},
    "RESEND_API_KEY": {"feature": "Email Notifications", "severity": "MEDIUM", "fallback": "Console Logs"},
    "INFISICAL_TOKEN": {"feature": "Secret Vault Sync", "severity": "CRITICAL", "fallback": ".env files"},
    "VITE_SUPABASE_URL": {"feature": "Frontend DB Client", "severity": "CRITICAL", "fallback": "None"},
    "VITE_SUPABASE_ANON_KEY": {"feature": "Frontend DB Auth", "severity": "CRITICAL", "fallback": "None"}
}

def load_env(env_path):
    keys = set()
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        keys.add(line.split("=")[0].strip())
    return keys

def main():
    print("\n" + "="*50)
    print(" [INFO] SupremeAI Feature Fuse Map Analysis")
    print("="*50 + "\n")
    
    # Check multiple locations
    env_paths = [Path(".env"), Path("backend/.env"), Path("frontend/.env")]
    active_keys = set(os.environ.keys())
    
    for path in env_paths:
        active_keys.update(load_env(path))
        
    blown_fuses = []
    active_fuses = []
    
    for key, info in FUSE_MAP.items():
        if key in active_keys:
            active_fuses.append((key, info))
        else:
            blown_fuses.append((key, info))
            
    print(f"[OK] Active Features ({len(active_fuses)}):")
    for key, info in active_fuses:
        print(f"  [OK] {key} -> {info['feature']}")
        
    print(f"\n[FAIL] BLOWN FUSES - Missing Keys ({len(blown_fuses)}):")
    if not blown_fuses:
        print("  All mapped features are fully powered!")
    else:
        for key, info in blown_fuses:
            color = "\033[91m" if info["severity"] == "CRITICAL" else "\033[93m"
            print(f"  {color}[{info['severity']}] {key}\033[0m")
            print(f"      Feature Disabled: {info['feature']}")
            print(f"      Fallback Action:  {info['fallback']}\n")

if __name__ == "__main__":
    main()
