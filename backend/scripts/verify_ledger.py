from loguru import logger
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.security.cryptographic_ledger import CryptographicLedger


def main():
    """
    Cryptographic Ledger Verification CLI Tool.
    """
    logger.debug("=== SupremeAI 2.0 Cryptographic Ledger Integrity Verification ===")
    ledger = CryptographicLedger()

    # Test entries
    ledger.record_entry_sync("agent_sentinel", "DEPLOY_MODEL", {"model": "gpt-4o", "tier": 1})
    ledger.record_entry_sync("agent_code", "GENERATE_PATCH", {"target": "auth.py", "lines": 12})

    logger.debug(f"Total Ledger Blocks: {len(ledger.chain)}")
    merkle_root = ledger.compute_merkle_root()
    logger.debug(f"Computed Merkle Root: {merkle_root}")

    is_valid = ledger.verify_chain_integrity()
    if is_valid:
        logger.debug("[SUCCESS] Cryptographic Ledger Chain Integrity Verified! Zero tampering detected.")
        sys.exit(0)
    else:
        logger.debug("[CRITICAL] Tampering detected in Cryptographic Ledger!")
        sys.exit(1)


if __name__ == "__main__":
    main()
