"""Universal Skill Schema (USS) — SupremeAI dynamic skill metadata.

বাংলা মন্তব্য:
AutoSkillCreator-এর AI-জেনারেটেড স্কিল মেটাডাটা যাচাই ও ধারণ করার জন্য Pydantic-
নির্ভরতা ছাড়াই হালকা, সেলফ-কন্টেইনড স্কিমা। কোনো ভারী ডিপেনডেন্সি না থাকায় যেকোনো
env-এ ইম্পোর্ট করা যায় (Zero Breakage নীতি)।

Contract সোর্স:
  - `core/evolution/auto_skill_creator.py` — UniversalSkillSchema(**schema_dict),
    `uss.metadata.version/description`, `uss.execution.dependencies`,
    `uss.validation.tests` (প্রতিটির `.input` / `.expected_output`)
  - `tests/test_uss.py` — semver যাচাই (`1.2` → ValueError) ও security_level যাচাই
    (`unrestricted` → ValueError), `.validation.security_level`
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
# "unrestricted" ইচ্ছাকৃতভাবে বাদ — যাতে নিজে-জেনারেটেড কোড সবসময় স্যান্ডবক্সে চলে।
_SECURITY_LEVELS = frozenset({"sandboxed", "restricted", "safe"})


@dataclass
class USSValidationTest:
    """একটি validation test-case: ইনপুট বনাম প্রত্যাশিত আউটপুট।"""

    input: Any = None
    expected_output: Any = None


@dataclass
class USSMetadata:
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = "supremeai_agent_id"
    tags: list[str] = field(default_factory=list)


@dataclass
class USSInterface:
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class USSExecution:
    runtime: str = "python3.11"
    entry_point: str = "main.execute"
    dependencies: list[str] = field(default_factory=list)
    timeout_seconds: int = 30


@dataclass
class USSValidation:
    tests: list[USSValidationTest] = field(default_factory=list)
    security_level: str = "sandboxed"


class UniversalSkillSchema:
    """USkill স্ট্রাকচারধারী স্কিমা — dict থেকে তৈরি হয়, attribute-access সমর্থন করে।

    `UniversalSkillSchema(**raw_dict)` প্যাটার্নে নির্মাণযোগ্য। সেমভার ও
    security_level যাচাই ব্যর্থ হলে `ValueError` রেইজ করে।
    """

    def __init__(
        self,
        metadata: dict[str, Any] | None = None,
        interface: dict[str, Any] | None = None,
        execution: dict[str, Any] | None = None,
        validation: dict[str, Any] | None = None,
        **extra: Any,
    ) -> None:
        self.metadata = USSMetadata(**(metadata or {}))
        self.interface = USSInterface(**(interface or {}))
        self.execution = USSExecution(**(execution or {}))

        validation = validation or {}
        raw_tests = validation.get("tests", [])
        tests = [
            t if isinstance(t, USSValidationTest) else USSValidationTest(**t)
            for t in raw_tests
        ]
        self.validation = USSValidation(
            tests=tests,
            security_level=validation.get("security_level", "sandboxed"),
        )
        self.extra = extra

        self._validate()

    def _validate(self) -> None:
        version = self.metadata.version
        if not _SEMVER_RE.match(str(version)):
            raise ValueError(f"Invalid semantic version: {version!r}")

        level = self.validation.security_level
        if level not in _SECURITY_LEVELS:
            raise ValueError(
                f"Invalid security_level: {level!r}. "
                f"Allowed: {sorted(_SECURITY_LEVELS)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """সম্পূর্ণ USS-কে dict-এ রূপান্তর (স্টোরেজ/ফায়ারস্টোরের জন্য)।"""
        return {
            "metadata": {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "description": self.metadata.description,
                "author": self.metadata.author,
                "tags": list(self.metadata.tags),
            },
            "interface": {
                "input_schema": dict(self.interface.input_schema),
                "output_schema": dict(self.interface.output_schema),
            },
            "execution": {
                "runtime": self.execution.runtime,
                "entry_point": self.execution.entry_point,
                "dependencies": list(self.execution.dependencies),
                "timeout_seconds": self.execution.timeout_seconds,
            },
            "validation": {
                "tests": [
                    {"input": t.input, "expected_output": t.expected_output}
                    for t in self.validation.tests
                ],
                "security_level": self.validation.security_level,
            },
        }


__all__ = [
    "UniversalSkillSchema",
    "USSMetadata",
    "USSInterface",
    "USSExecution",
    "USSValidation",
    "USSValidationTest",
]
