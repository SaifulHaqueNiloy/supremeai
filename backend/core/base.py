"""This module establishes the fundamental `BaseSkill` abstract base class, serving as the core contract for all executable skills within the SupremeAI ecosystem. It mandates that every concrete skill implementation must provide an asynchronous `execute` method, thereby standardizing the interface for agents to interact with and leverage diverse capabilities across the platform. This foundational structure is crucial for maintaining consistency and interoperability among the various agentic tools.

Key Components:
- `BaseSkill`: An abstract base class that defines the essential interface and contract for all skills, ensuring they adhere to a common structure and implement core execution logic.
- `BaseSkill.execute()`: An abstract asynchronous method that concrete skill implementations must override to encapsulate their specific operational logic and return a result.
- `BaseSkill.name`: A property that provides the string name of the skill, typically derived from its class name, for identification purposes.

Dependencies:
- `abc`: Utilized for defining abstract base classes (`ABC`) and abstract methods (`abstractmethod`), enforcing the skill contract.
- `typing`: Used for type hinting, specifically `Any`, to indicate flexible input and output types for skill execution.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSkill(ABC):
    """
    বাংলা মন্তব্ট: সকল স্কিলের জন্য অ্যাবস্ট্র্যাক্ট বেস ক্লাস (The Contract)।
    প্রতিটি স্কিলকে অবশ্যই একটি async `execute` মেথড ইমপ্লিমেন্ট করতে হবে।
    """

    parameters: list[dict[str, Any]] = []

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        বাংলা মন্তব্ট: এই মেথডটি স্কিলের মূল লজিক ধারণ করবে।
        """
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def get_schema(self) -> list[dict[str, Any]]:
        """Return the parameter schema for this skill."""
        return self.parameters

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate and sanitize arguments against the skill's parameter schema."""
        schema = self.get_schema()
        if not schema:
            return args

        validated: dict[str, Any] = {}

        for param in schema:
            pname = param["name"]
            ptype = param.get("type", "string")
            has_default = "default" in param

            if pname not in args:
                if not has_default:
                    raise ValueError(f"Missing required parameter: {pname}")
                validated[pname] = param["default"]
                continue

            raw = args[pname]
            try:
                if ptype == "string":
                    validated[pname] = str(raw)
                elif ptype == "integer":
                    validated[pname] = int(float(raw)) if isinstance(raw, str) else int(raw)
                elif ptype == "number":
                    validated[pname] = float(raw)
                elif ptype == "boolean":
                    if isinstance(raw, str):
                        validated[pname] = raw.lower() in ("true", "1", "yes")
                    else:
                        validated[pname] = bool(raw)
                else:
                    validated[pname] = raw
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Parameter '{pname}': cannot coerce {raw!r} to {ptype}: {exc}"
                ) from exc

        return validated
