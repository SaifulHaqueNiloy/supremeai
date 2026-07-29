"""
Coverage tests for core/security/secret_vault.py.
Target: 100% line coverage.

সিক্রেট ভল্ট মডিউলের সকল ফাংশন ও শাখা কভার করা হয়েছে।
"""

import os
import sys

import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class TestSecretVault:
    """Tests for ProductionSecretVault."""

    def test_init(self):
        """ProductionSecretVault should initialize with config."""
        from core.security.secret_vault import ProductionSecretVault

        vault = ProductionSecretVault()
        assert vault is not None

    def test_get_secret_env_fallback(self):
        """get_secret should fallback to environment variable."""
        from core.security.secret_vault import ProductionSecretVault

        os.environ["TEST_VAULT_KEY"] = "env_value"
        vault = ProductionSecretVault()
        result = vault.get_secret("TEST_VAULT_KEY")
        assert result == "env_value"
        del os.environ["TEST_VAULT_KEY"]

    def test_get_secret_not_found(self):
        """get_secret should return a fallback for missing key in test env."""
        from core.security.secret_vault import ProductionSecretVault

        vault = ProductionSecretVault()
        result = vault.get_secret("NONEXISTENT_KEY_XYZ")
        assert result is not None
        assert isinstance(result, str)

    def test_set_secret(self):
        """set_secret should store secret in cache."""
        from core.security.secret_vault import ProductionSecretVault

        vault = ProductionSecretVault()
        vault.set_secret("TEST_KEY", "test_value")
        result = vault.get_secret("TEST_KEY")
        assert result == "test_value"

    def test_delete_secret(self):
        """delete_secret should remove secret from cache."""
        from core.security.secret_vault import ProductionSecretVault

        vault = ProductionSecretVault()
        vault.set_secret("TEST_KEY", "test_value")
        vault.delete_secret("TEST_KEY")
        result = vault.get_secret("TEST_KEY")
        # After delete, should not find it anymore
        assert result is None or result != "test_value"

    def test_list_secrets(self):
        """list_secrets should return all secret keys."""
        from core.security.secret_vault import ProductionSecretVault

        vault = ProductionSecretVault()
        vault.set_secret("KEY_1", "val1")
        vault.set_secret("KEY_2", "val2")
        secrets = vault.list_secrets()
        assert "KEY_1" in secrets
        assert "KEY_2" in secrets

    def test_invalidate_cache(self):
        """invalidate_cache should clear all cached secrets."""
        from core.security.secret_vault import ProductionSecretVault

        vault = ProductionSecretVault()
        vault.set_secret("TEST_KEY", "test_value")
        vault.invalidate_cache()
        result = vault.get_secret("TEST_KEY")
        assert result is None or result != "test_value"

    @pytest.mark.asyncio
    async def test_fetch_async(self):
        """fetch_secret_async should return secret asynchronously."""
        from core.security.secret_vault import ProductionSecretVault

        vault = ProductionSecretVault()
        vault.set_secret("TEST_KEY", "async_value")
        result = await vault.fetch_secret_async("TEST_KEY")
        assert result == "async_value"


class TestSecureCredentialStore:
    """Tests for SecureCredentialStore."""

    def test_init(self):
        """SecureCredentialStore should initialize."""
        from core.security.secure_credential_store import SecureCredentialStore

        store = SecureCredentialStore()
        assert store is not None

    def test_encrypt_decrypt_roundtrip(self):
        """encrypt and decrypt should work as a roundtrip."""
        from core.security.secure_credential_store import SecureCredentialStore

        store = SecureCredentialStore()
        ciphertext, key_ref = store.encrypt("sensitive_data")
        assert ciphertext is not None
        assert ciphertext != "sensitive_data" or not store.provider.enabled

        decrypted = store.decrypt(ciphertext, key_ref)
        assert decrypted == "sensitive_data"

    def test_mask(self):
        """mask should hide part of the string."""
        from core.security.secure_credential_store import SecureCredentialStore

        store = SecureCredentialStore()
        masked = store.mask("secret123")
        assert masked != "secret123"
        assert "*" in masked
        assert masked.startswith("secr")
        assert masked.endswith("*")
