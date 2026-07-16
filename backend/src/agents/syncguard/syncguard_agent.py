import yaml
from pathlib import Path
from typing import Dict, Any
from .tools import check_infrastructure_drift, check_env_secrets_sync, check_redis_connection

class SyncGuardAgent:
    def __init__(self, llm_client=None):
        """
        Initialize the SyncGuard Agent with its config and LLM client.
        """
        self.llm_client = llm_client
        self.config = self._load_config()
        self.name = self.config.get("name", "SyncGuard")

    def _load_config(self) -> dict:
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    async def run_full_audit(self) -> Dict[str, Any]:
        """
        Executes the full synchronization audit across the 10-Crore-Floor architecture.
        """
        print(f"\n🚀 [{self.name}] Initiating System Audit...")
        audit_report = {"status": "SYNC_OK", "issues": []}

        # 1. Check Infrastructure Blueprint Sync
        infra_status = await check_infrastructure_drift("github.com/paykaribazaronline/supremeai")
        if infra_status["status"] != "matched":
            audit_report["status"] = "SYNC_FAILED"
            audit_report["issues"].append("Infrastructure Blueprint Drift Detected.")

        # 2. Check Environment Variables (The critical keys from your blueprint)
        required_env_keys = ["REDIS_URL", "OPENAI_API_KEY", "SUPABASE_URL"]
        env_status = await check_env_secrets_sync(required_env_keys)
        if env_status["status"] != "synced":
            audit_report["status"] = "SYNC_FAILED"
            audit_report["issues"].append(f"Missing Env Secrets: {env_status['missing']}")

        # 3. Check Message Broker (Upstash Redis)
        redis_alive = await check_redis_connection(os.getenv("REDIS_URL", "dummy_url"))
        if not redis_alive:
            audit_report["status"] = "SYNC_FAILED"
            audit_report["issues"].append("Redis Message Broker is unreachable.")

        # Final Decision
        if audit_report["status"] == "SYNC_FAILED":
            print(f"❌ [{self.name}] AUDIT FAILED. System is out of sync!")
            print(f"Details: {audit_report['issues']}")
        else:
            print(f"✅ [{self.name}] AUDIT PASSED. System is 100% synchronized and ready for scaling.")

        return audit_report

# Test Execution (If run directly)
if __name__ == "__main__":
    import asyncio
    agent = SyncGuardAgent()
    asyncio.run(agent.run_full_audit())
