# backend/evolution/auto_skill_creator.py
"""Auto Skill Creator with AST Sandbox for SupremeAI.

Provides:
- SecuritySandbox: Validates Python AST before execution
- AutoSkillCreator: Generates and safely tests new AI skills
- MaliciousCodeError: Exception for banned imports
- SkillExecutionError: Exception for execution failures
"""

from __future__ import annotations

import ast
import os
import subprocess
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import settings
from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus


class MaliciousCodeError(Exception):
    """Raised when generated code contains banned imports or malicious patterns."""

    pass


class SkillExecutionError(Exception):
    """Raised when skill execution fails or times out."""

    pass


class SecuritySandbox:
    """
    Validates Python AST (Abstract Syntax Tree) before execution.

    বাংলা মন্তব্য: এআই যে কোডই জেনারেট করুক না কেন, রান করার আগে এই মডিউলটি কোড স্ক্যান করে ক্ষতিকর লাইব্রেরি ব্লক করে।
    """

    BANNED_IMPORTS: set[str] = {
        "os",
        "subprocess",
        "sys",
        "shutil",
        "socket",
        "requests",
        "urllib",
        "http",
        "ftplib",
        "telnetlib",
        "smtplib",
        "poplib",
        "imaplib",
        "nntplib",
        "pickle",
        "shelve",
        "marshal",
        "ctypes",
        "multiprocessing",
        "threading",
        "asyncio",
    }

    BANNED_BUILTINS: set[str] = {
        "eval",
        "exec",
        "compile",
        "open",
        "__import__",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
    }

    @classmethod
    def validate_code(cls, code_string: str) -> bool:
        """
        Validate Python code by parsing AST and checking for banned imports.

        Args:
            code_string: The Python code to validate

        Returns:
            True if code is safe

        Raises:
            MaliciousCodeError: If code contains banned imports or patterns
        """
        try:
            tree = ast.parse(code_string)
            for node in ast.walk(tree):
                # Check for import statements
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        if module_name in cls.BANNED_IMPORTS:
                            raise MaliciousCodeError(
                                f"Banned import detected: {alias.name}"
                            )
                # Check for from-import statements
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split(".")[0]
                        if module_name in cls.BANNED_IMPORTS:
                            raise MaliciousCodeError(
                                f"Banned from-import detected: {node.module}"
                            )
                # Check for banned builtin calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in cls.BANNED_BUILTINS:
                            raise MaliciousCodeError(
                                f"Banned builtin call detected: {node.func.id}"
                            )
            return True
        except SyntaxError as e:
            raise MaliciousCodeError(f"Syntax error in generated code: {e}") from e


class AutoSkillCreator:
    """
    Generates and safely tests new AI skills.

    বাংলা মন্তব্য: এআই-জেনারেটেড কোড ভ্যালিডেট, সেভ এবং আইসোলেটেড সাবপ্রসেসে নিরাপদে এক্সিকিউট করে।
    """

    def __init__(self) -> None:
        self.skills_dir = Path("skills/generated")
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._execution_timeout: float = 5.0  # Strict 5s timeout

    async def save_and_test_skill(
        self,
        skill_name: str,
        code: str,
    ) -> str:
        """
        Validates, saves, and strictly executes the skill via isolated subprocess.

        Args:
            skill_name: Name of the skill (sanitized for file path)
            code: Python code to execute

        Returns:
            stdout from the executed code

        Raises:
            MaliciousCodeError: If code contains banned imports
            SkillExecutionError: If execution fails or times out
        """
        # 1. AST Validation
        SecuritySandbox.validate_code(code)

        # 2. Strict Path Whitelist Check
        safe_filename = "".join(
            c for c in skill_name if c.isalnum() or c in ("_", "-")
        ).rstrip()
        if not safe_filename:
            raise MaliciousCodeError("Invalid skill name")

        file_path = self.skills_dir / f"{safe_filename}.py"

        # Ensure path is within skills directory (prevent path traversal)
        try:
            file_path.resolve().relative_to(self.skills_dir.resolve())
        except ValueError as e:
            raise MaliciousCodeError(
                "Path traversal attempt detected in skill name."
            ) from e

        # 3. Save Code
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            error_event_bus.emit(
                ErrorEvent(
                    module="AutoSkillCreator",
                    error_type="FILE_SAVE_ERROR",
                    message=str(e)[:500],
                    severity="ERROR",
                    context={"skill_name": skill_name},
                    structured_context=ErrorContext(
                        module="evolution.auto_skill_creator",
                        env=settings.env,
                    ),
                )
            )
            raise SkillExecutionError(f"Failed to save skill: {e}") from e

        # 4. Encapsulated Execution Guard (Timeout & Check)
        try:
            result = subprocess.run(
                ["python", str(file_path)],
                capture_output=True,
                text=True,
                timeout=self._execution_timeout,
                check=True,  # Throws CalledProcessError on non-zero exit
            )
            return result.stdout

        except subprocess.TimeoutExpired as e:
            # Auto-cleanup bad code
            self._cleanup_skill(file_path)
            error_event_bus.emit(
                ErrorEvent(
                    module="AutoSkillCreator",
                    error_type="SKILL_TIMEOUT",
                    message=f"Skill execution timed out after {self._execution_timeout}s",
                    severity="WARNING",
                    context={"skill_name": skill_name},
                    structured_context=ErrorContext(
                        module="evolution.auto_skill_creator",
                        env=settings.env,
                    ),
                )
            )
            raise SkillExecutionError(
                "Skill execution timed out (possible infinite loop)."
            ) from e

        except subprocess.CalledProcessError as e:
            # Auto-cleanup bad code
            self._cleanup_skill(file_path)
            error_event_bus.emit(
                ErrorEvent(
                    module="AutoSkillCreator",
                    error_type="SKILL_EXECUTION_FAILED",
                    message=str(e.stderr)[:500] if e.stderr else "Unknown error",
                    severity="ERROR",
                    context={"skill_name": skill_name, "exit_code": e.returncode},
                    structured_context=ErrorContext(
                        module="evolution.auto_skill_creator",
                        env=settings.env,
                    ),
                )
            )
            raise SkillExecutionError(
                f"Skill execution failed: {e.stderr}"
            ) from e

        except Exception as e:
            # Auto-cleanup on any error
            self._cleanup_skill(file_path)
            error_event_bus.emit(
                ErrorEvent(
                    module="AutoSkillCreator",
                    error_type="SKILL_ERROR",
                    message=str(e)[:500],
                    severity="ERROR",
                    context={"skill_name": skill_name},
                    structured_context=ErrorContext(
                        module="evolution.auto_skill_creator",
                        env=settings.env,
                    ),
                )
            )
            raise SkillExecutionError(f"Unexpected error: {e}") from e

    def _cleanup_skill(self, file_path: Path) -> None:
        """Remove skill file on error."""
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup skill file {file_path}: {e}")
