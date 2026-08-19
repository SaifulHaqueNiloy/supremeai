import uuid
from typing import Any

from loguru import logger


class InsufficientCreditsError(Exception):
    """Raised when a consumer does not have enough P2P credits for a task."""


class CreditLedger:
    """In-memory credit ledger for P2P compute sharing.

    Balances are kept in a plain dict so the module is fully functional
    without external services. Swap the storage layer for Redis/persistent
    backing later without changing callers.
    """

    def __init__(self) -> None:
        self._balances: dict[str, float] = {}

    def balance(self, user_id: str) -> float:
        return self._balances.get(user_id, 0.0)

    def _adjust(self, user_id: str, amount: float) -> float:
        self._balances[user_id] = self.balance(user_id) + amount
        return self._balances[user_id]

    async def deduct_credits(self, user_id: str, amount: float, reason: str = "") -> dict[str, Any]:
        if self.balance(user_id) < amount:
            raise InsufficientCreditsError(
                f"User {user_id} has insufficient credits "
                f"(has {self.balance(user_id)}, needs {amount})"
            )
        new_balance = self._adjust(user_id, -amount)
        return {
            "tx_id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": -amount,
            "reason": reason,
            "type": "debit",
            "balance": new_balance,
        }

    async def add_credits(self, user_id: str, amount: float, reason: str = "") -> dict[str, Any]:
        new_balance = self._adjust(user_id, amount)
        return {
            "tx_id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": amount,
            "reason": reason,
            "type": "credit",
            "balance": new_balance,
        }

    # Backwards-compatible convenience wrappers kept from the prior refactor.
    async def earn(self, user_id: str, amount: float, reason: str) -> dict[str, Any]:
        return await self.add_credits(user_id, amount, reason)

    async def spend(self, user_id: str, amount: float, reason: str) -> dict[str, Any]:
        return await self.deduct_credits(user_id, amount, reason)

    async def opt_out(self, user_id: str) -> None:
        logger.info(f"User {user_id} opted out of P2P")

    async def opt_in(self, user_id: str) -> None:
        logger.info(f"User {user_id} opted in to P2P")


class ResourceBroker:
    async def match(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"matched": False, "reason": "no_available_peers"}


# Module-level singleton used by p2p/resource_broker.py
credit_system = CreditLedger()
