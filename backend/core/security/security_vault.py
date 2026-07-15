import os

from cryptography.fernet import Fernet
from loguru import logger

from core.messaging.event_bus import ErrorEvent
from core.messaging.event_bus import error_event_bus
from core.security.secure_credential_store import RotatingFernet


# বাংলা মন্তব্য: Module-level key read-এ fail-fast রাখা হচ্ছে, কারণ ক্রিপ্টোগ্রাফি স্টার্টআপেই ফেইল হওয়া উচিত।
# তবে ENCRYPTION_KEY যেন settings থেকে আসে তা নিশ্চিত করতে হবে, আপাতত os.environ.get ব্যবহার করলেও fail-fast আছে।
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # বাংলা মন্তব্য: টেস্ট ও সিআই পরিবেশে ক্র্যাশ এড়াতে একটি ডামি/এফেমেরাল কী জেনারেট করা হচ্ছে, তবে প্রোডাকশনে ফেইল-ফাস্ট থাকবে।
    if (os.environ.get("ENV") == "test" or os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true") and os.environ.get(
        "STRICT_ENCRYPTION_CHECK"
    ) != "true":
        ENCRYPTION_KEY = Fernet.generate_key().decode("utf-8")
    else:
        error_event_bus.emit(
            ErrorEvent(
                module="security_vault",
                error_type="MISSING_ENCRYPTION_KEY",
                message="ENCRYPTION_KEY environment variable is missing",
                severity="CRITICAL",
            )
        )
        raise ValueError("CRITICAL: ENCRYPTION_KEY environment variable is not set. Halting application for security reasons. Fail-Fast!")

# বাংলা মন্তব্য: ENCRYPTION_KEYS, ENCRYPTION_KEY এবং SUPREMEAI_CREDENTIAL_ENC_KEY সব চেক করা হচ্ছে রোটেশনের জন্য।
_raw_keys = [
    k for k in os.environ.get(
        "ENCRYPTION_KEYS",
        os.environ.get("SUPREMEAI_CREDENTIAL_ENC_KEY", ENCRYPTION_KEY or "")
    ).split(",") if k.strip()
]

if not _raw_keys:
    raise ValueError("CRITICAL: No encryption keys configured (ENCRYPTION_KEYS). Fail-Fast!")

# বাংলা মন্তব্য: RotatingFernet একমাত্র সেন্ট্রাল ক্রিপ্টোগ্রাফি ইঞ্জিন হিসেবে সেট হলো।
_vault = RotatingFernet(_raw_keys)


def encrypt_token(plain_text: str) -> str:
    """Encrypts a token using AES (Fernet) via central RotatingFernet."""
    if not plain_text:
        return ""
    try:
        return _vault.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error encrypting token: {e}")
        error_event_bus.emit(ErrorEvent(module="security_vault", error_type="ENCRYPTION_FAILED", message=str(e)[:200], severity="ERROR"))
        raise RuntimeError("Token encryption failed.") from e


def decrypt_token(cipher_text: str, ttl: int | None = None) -> str:
    """Decrypts a token using AES (Fernet) via central RotatingFernet.

    বাংলা মন্তব্য: OAuth দীর্ঘমেয়াদী টোকেনের মেয়াদোত্তীর্ণ এড়াতে ডিফল্ট ttl=None রাখা হয়েছে।
    """
    if not cipher_text:
        return ""
    try:
        return _vault.decrypt(cipher_text.encode("utf-8"), ttl=ttl).decode("utf-8")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error decrypting token: {e}")
        error_event_bus.emit(ErrorEvent(module="security_vault", error_type="DECRYPTION_FAILED", message=str(e)[:200], severity="CRITICAL"))
        raise ValueError("Decryption failed: Invalid or corrupted token.") from e
