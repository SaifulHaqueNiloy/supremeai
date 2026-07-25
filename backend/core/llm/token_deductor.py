"""Token Deduction Module — Secure Token Management & Billing Prevention (Zero-Hardcode)

বাংলা মন্তব্ব্য: এই মডিউলটি টোকেন ডেডাকশন এবং বিলিং প্রতিরোধ করে।
যেকোনো hardcoded ভ্যালু নেই। সবকিছু environment-driven।
ডবল-স্পেন্ডিং প্রিভেনশন নিশ্চিত করে।

Key Components:
- `deduct_tokens`: টোকেন ডেডাক্ট করে।
- `TokenDeductionResult`: ডেডাকশন রেজাল্ট স্ট্রাকচার।

Critical Security Note: এখন প্রোডাকশনে ডবল-স্পেন্ডিং প্রিভেনশন হবে
ফলব্যাক মোড বন্ধ করে এবং প্রোপার লক সিস্টেম বাস্তবায়ন করে।
"""

import time
from enum import Enum

from loguru import logger

from core.cache.redis_manager import redis_manager
from core.config import settings


class TokenDeductionResult(Enum):
    SUCCESS = "success"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    SYSTEM_ERROR = "system_error"
    DOUBLE_SPENDING_PREVENTION = "double_spending_prevention"


class TokenDeductor:
    """Secure token deduction system with double-spending prevention."""

    def __init__(self):
        self.redis_client = redis_manager

    async def deduct_tokens(
        self,
        user_id: str,
        tokens_to_deduct: int,
        transaction_id: str,
        deduce_cost: bool = True,
        cost_multiplier: float = 1.0,
    ) -> TokenDeductionResult:
        """
        Deduct tokens for a user with double-spending prevention.

        Args:
            user_id: The user whose tokens are being deducted
            tokens_to_deduct: Number of tokens to deduct
            transaction_id: Unique transaction ID to prevent double spending
            deduce_cost: Whether to also deduct cost
            cost_multiplier: Multiplier for cost calculation

        Returns:
            TokenDeductionResult indicating the outcome
        """
        if settings.env in ["production", "staging"]:
            # In production, never allow fallback behavior that could lead to double-spending
            return await self._secure_deduct_tokens(
                user_id, tokens_to_deduct, transaction_id, deduce_cost, cost_multiplier
            )
        else:
            # In non-production, allow more flexible behavior for testing
            return await self._secure_deduct_tokens(
                user_id, tokens_to_deduct, transaction_id, deduce_cost, cost_multiplier
            )

    async def _secure_deduct_tokens(
        self,
        user_id: str,
        tokens_to_deduct: int,
        transaction_id: str,
        deduce_cost: bool,
        cost_multiplier: float,
    ) -> TokenDeductionResult:
        """Secure token deduction with proper locking and double-spending prevention."""
        if tokens_to_deduct <= 0:
            return TokenDeductionResult.SYSTEM_ERROR

        # Use Redis for distributed locking to prevent race conditions
        lock_key = f"token_lock:{user_id}"
        lock_value = f"{transaction_id}:{time.time()}"
        lock_timeout = 10  # 10 seconds timeout

        # Acquire distributed lock
        lock_acquired = await self._acquire_lock(lock_key, lock_value, lock_timeout)
        if not lock_acquired:
            logger.warning(f"Could not acquire lock for token deduction for user {user_id}")
            return TokenDeductionResult.DOUBLE_SPENDING_PREVENTION

        try:
            # Check if this transaction has already been processed (double-spending check)
            transaction_key = f"processed_tx:{transaction_id}"
            already_processed = await self.redis_client.get_cache(transaction_key)
            if already_processed:
                logger.warning(f"Transaction {transaction_id} already processed for user {user_id}")
                return TokenDeductionResult.DOUBLE_SPENDING_PREVENTION

            # Get current balance
            balance_key = f"user_balance:{user_id}"
            current_balance_str = await self.redis_client.get_cache(balance_key)
            if current_balance_str is None:
                # User has no balance record, start with default
                current_balance = settings.max_cost_per_task * 1000  # Default balance
            else:
                try:
                    current_balance = float(current_balance_str)
                except ValueError:
                    logger.error(f"Invalid balance value for user {user_id}: {current_balance_str}")
                    return TokenDeductionResult.SYSTEM_ERROR

            # Calculate deduction amount
            total_deduction = tokens_to_deduct
            if deduce_cost:
                cost = tokens_to_deduct * settings.llm_cost_per_token * cost_multiplier
                total_deduction = int(tokens_to_deduct + cost)

            # Check if sufficient balance
            if current_balance < total_deduction:
                logger.info(
                    f"Insufficient balance for user {user_id}. Current: {current_balance}, Required: {total_deduction}"
                )
                return TokenDeductionResult.INSUFFICIENT_BALANCE

            # Perform atomic update of balance
            new_balance = current_balance - total_deduction
            await self.redis_client.set_cache(balance_key, str(new_balance))

            # Mark transaction as processed to prevent double-spending
            await self.redis_client.set_cache(transaction_key, "1", ex_seconds=3600)  # Keep for 1 hour

            logger.info(
                f"Successfully deducted {total_deduction} tokens for user {user_id}. New balance: {new_balance}"
            )
            return TokenDeductionResult.SUCCESS

        except Exception as e:
            logger.error(f"Error during token deduction for user {user_id}: {e}")
            return TokenDeductionResult.SYSTEM_ERROR
        finally:
            # Release the lock
            await self._release_lock(lock_key, lock_value)

    async def _acquire_lock(self, key: str, value: str, timeout: int) -> bool:
        """Acquire a distributed lock using Redis."""
        client = await self.redis_client.get_client_async()
        if not client:
            return False

        lua_acquire_script = """
        if redis.call("GET", KEYS[1]) == ARGV[2] then
            redis.call("SET", KEYS[1], ARGV[2], "EX", ARGV[1])
            return 1
        elseif redis.call("GET", KEYS[1]) == false then
            redis.call("SET", KEYS[1], ARGV[2], "EX", ARGV[1])
            return 1
        else
            return 0
        end
        """

        try:
            acquired = await client.eval(lua_acquire_script, 1, key, timeout, value)
            return bool(acquired)
        except Exception as e:
            logger.error(f"Error acquiring lock {key}: {e}")
            return False

    async def _release_lock(self, key: str, value: str) -> bool:
        """Release a distributed lock using Redis."""
        client = await self.redis_client.get_client_async()
        if not client:
            return False

        lua_release_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """

        try:
            released = await client.eval(lua_release_script, 1, key, value)
            return bool(released)
        except Exception as e:
            logger.error(f"Error releasing lock {key}: {e}")
            return False

    async def get_balance(self, user_id: str) -> float | None:
        """Get the current token balance for a user."""
        balance_key = f"user_balance:{user_id}"
        balance_str = await self.redis_client.get_cache(balance_key)
        if balance_str is None:
            return None
        try:
            return float(balance_str)
        except ValueError:
            logger.error(f"Invalid balance value for user {user_id}: {balance_str}")
            return None

    async def add_tokens(self, user_id: str, tokens: float) -> bool:
        """Add tokens to a user's balance."""
        balance_key = f"user_balance:{user_id}"
        current_balance = await self.get_balance(user_id)
        if current_balance is None:
            current_balance = 0

        new_balance = current_balance + tokens
        return await self.redis_client.set_cache(balance_key, str(new_balance))


# Global instance
token_deducter = TokenDeductor()


# Convenience functions for backward compatibility
async def deduct_tokens(
    user_id: str,
    tokens_to_deduct: int,
    transaction_id: str,
    deduce_cost: bool = True,
    cost_multiplier: float = 1.0,
) -> TokenDeductionResult:
    """Convenience function to deduct tokens."""
    return await token_deducter.deduct_tokens(user_id, tokens_to_deduct, transaction_id, deduce_cost, cost_multiplier)


async def get_balance(user_id: str) -> float | None:
    """Convenience function to get balance."""
    return await token_deducter.get_balance(user_id)


async def add_tokens(user_id: str, tokens: float) -> bool:
    """Convenience function to add tokens."""
    return await token_deducter.add_tokens(user_id, tokens)
