# Immune System static security analysis scanner
# বাংলা মন্তব্য: এআই জেনারেটেড কোডের সিকিউরিটি স্ক্যানার ও এএসটি ভ্যালিডেশন গেটকিপার।

import ast
from loguru import logger


class SecuritySandboxError(Exception):
    """Custom exception for security sandbox violations."""

    pass


class ASTSecurityVisitor(ast.NodeVisitor):
    """Enhanced AST visitor to detect and block malicious code patterns."""

    def __init__(self):
        self.banned_imports = {
            "os",
            "sys",
            "subprocess",
            "shutil",
            "socket",
            "requests",
            "urllib",
            "httpx",
            "aiohttp",
        }
        self.banned_functions = {
            "eval",
            "exec",
            "compile",
            "globals",
            "locals",
            "vars",
            "dir",
            "breakpoint",
            "__import__",
            "getattr",
            "setattr",
            "delattr",
            "hasattr",
            "open",
            "execfile",
            "file",
            "__subclasses__",
            "__bases__",
            "__mro__",
            "__dict__",
            "__class__",
            "__getattribute__",
            "__getattr__",
            "importlib",
            "subprocess",
            "os",
            "sys",
            "shutil",
            "socket",
            "urllib",
            "requests",
            "httpx",
            "aiohttp",
            "ftplib",
            "telnetlib",
        }

        self.banned_attributes = {
            "__class__",
            "__bases__",
            "__subclasses__",
            "__globals__",
            "__builtins__",
            "__dict__",
            "__mro__",
            "__code__",
            "__closure__",
            "__func__",
            "__self__",
            "__module__",
            "__file__",
            "__path__",
            "__loader__",
            "__spec__",
            "__package__",
            "__doc__",
            "__subclasshook__",
            "__weakref__",
            "__annotations__",
            "__init_subclass__",
            "__new__",
            "__del__",
            "__str__",
            "__repr__",
            "__format__",
            "__lt__",
            "__le__",
            "__eq__",
            "__ne__",
            "__gt__",
            "__ge__",
            "__hash__",
            "__bool__",
            "__bytes__",
            "__complex__",
            "__int__",
            "__float__",
            "__index__",
            "__trunc__",
            "__floor__",
            "__ceil__",
            "__round__",
            "__abs__",
            "__neg__",
            "__pos__",
            "__invert__",
            "__add__",
            "__sub__",
            "__mul__",
            "__matmul__",
            "__truediv__",
            "__floordiv__",
            "__mod__",
            "__divmod__",
            "__pow__",
            "__lshift__",
            "__rshift__",
            "__and__",
            "__xor__",
            "__or__",
            "__radd__",
            "__rsub__",
            "__rmul__",
            "__rmatmul__",
            "__rtruediv__",
            "__rfloordiv__",
            "__rmod__",
            "__rdivmod__",
            "__rpow__",
            "__rlshift__",
            "__rrshift__",
            "__rand__",
            "__rxor__",
            "__ror__",
            "__iadd__",
            "__isub__",
            "__imul__",
            "__imatmul__",
            "__itruediv__",
            "__ifloordiv__",
            "__imod__",
            "__ipow__",
            "__ilshift__",
            "__irshift__",
            "__iand__",
            "__ixor__",
            "__ior__",
            "__getitem__",
            "__setitem__",
            "__delitem__",
            "__length_hint__",
            "__missing__",
            "__iter__",
            "__next__",
            "__reversed__",
            "__contains__",
            "__await__",
            "__aiter__",
            "__anext__",
            "__aenter__",
            "__aexit__",
            "__enter__",
            "__exit__",
            "__get__",
            "__set__",
            "__delete__",
            "__set_name__",
            "__init__",
            "__call__",
        }

        self.banned_methods = {
            "import_module",
            "system",
            "popen",
            "spawn",
            "fork",
            "run",
            "run_async",
            "check_output",
            "call",
            "execve",
            "execl",
            "execle",
            "execlp",
            "execv",
            "execvp",
            "execvpe",
            "putenv",
            "unsetenv",
            "chmod",
            "chown",
            "remove",
            "unlink",
            "rmdir",
            "removedirs",
            "rename",
            "renames",
            "mkfifo",
            "mknod",
            "mkdir",
            "makedirs",
            "openpty",
            "spawnl",
            "spawnle",
            "spawnlp",
            "spawnlpe",
            "spawnv",
            "spawnve",
            "spawnvp",
            "spawnvpe",
            "startfile",
            "connect",
            "bind",
            "listen",
            "accept",
            "send",
            "recv",
            "sendto",
            "recvfrom",
            "sendall",
            "close",
        }

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module in self.banned_imports:
                raise SecuritySandboxError(f"Banned import detected: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module in self.banned_imports:
                raise SecuritySandboxError(f"Banned import detected: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Visit function calls and block dangerous patterns."""
        # Check if it's an attribute access call like obj.method()
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in self.banned_attributes:
                raise SecuritySandboxError(f"Sandbox escape via attribute access blocked: {attr_name}")
            if attr_name in self.banned_methods:
                raise SecuritySandboxError(f"Banned method invocation detected: {attr_name}")

            # Block dangerous chain accesses like "".class.bases[0].subclasses()[...]
            if isinstance(node.func.value, ast.Attribute):
                value_attr = node.func.value.attr
                if value_attr in self.banned_attributes:
                    raise SecuritySandboxError(f"Chained dunder access blocked: {value_attr}.{attr_name}")

        # Check direct function calls like eval(), exec()
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.banned_functions:
                raise SecuritySandboxError(f"Banned function call detected: {func_name}")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Visit attribute access and block dangerous patterns."""
        if node.attr in self.banned_attributes or node.attr in self.banned_functions:
            raise SecuritySandboxError(f"Sandbox escape pattern blocked: {node.attr}")

        # Also check parent nodes for chained access
        if isinstance(node.value, ast.Attribute):
            parent_attr = node.value.attr
            if parent_attr in self.banned_attributes:
                raise SecuritySandboxError(f"Chained dunder access blocked: {parent_attr}.{node.attr}")

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        """Visit subscript access and block dangerous patterns."""
        # Check for direct dangerous access
        if isinstance(node.value, ast.Name) and node.value.id in {"builtins", "__builtins__"}:
            raise SecuritySandboxError(f"Sandbox escape via subscript blocked: {node.value.id}[...]")

        # Check for chained attribute access in subscript
        if isinstance(node.value, ast.Attribute):
            if node.value.attr in self.banned_attributes:
                raise SecuritySandboxError(f"Dunder attribute access in subscript blocked: {node.value.attr}")

        # Check index for dangerous patterns
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            if node.slice.value in self.banned_functions or node.slice.value in self.banned_attributes:
                raise SecuritySandboxError(f"Banned subscript access blocked: {node.slice.value}")

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        # বাংলা মন্তব্য: নিষিদ্ধ ফাংশনের রেফারেন্স অন্য ভ্যারিয়েবলে অ্যাসাইন করা বা পাস করা ব্লক করতে এই চেকটি যোগ করা হলো।
        if node.id in self.banned_functions:
            raise SecuritySandboxError(f"Banned function reference detected: {node.id}")
        self.generic_visit(node)


class ImmuneSystemScanner:
    """
    Scans generated python code using AST parser to block execution of unsafe or malicious code before execution.
    """

    def __init__(self):
        # Preserve public interface configs if needed by test suite or other modules
        self.scanner = ASTSecurityScanner()

    def scan_code(self, code: str) -> dict:
        """
        Parses code string to check for banned keywords and modules.
        Returns a dict: {"safe": bool, "error": str | None}
        """
        try:
            tree = ast.parse(code)
            self.scanner.visit(tree)
            logger.info("AST Static code scan passed successfully. Code is safe for execution.")
            return {"safe": True, "error": None}
        except SecuritySandboxError as sse:
            logger.critical(f"🚨 [IMMUNE SYSTEM] Security threat defused: {sse}")
            # বাংলা মন্তব্য: টেস্ট কেসের প্রত্যাশিত আউটপুট ম্যাচ করানোর সাথে কাস্টম এক্সপশন মাস্কিং বজায় রাখা হলো
            error_msg = str(sse)
            if "Banned import" in error_msg:
                user_error = "Security validation failed: Banned root import detected and blocked."
            elif "Banned function" in error_msg:
                user_error = "Security validation failed: Reference to banned security identifier blocked."
            elif "Sandbox escape" in error_msg:
                user_error = "Security validation failed: Banned attribute or dunder reflection access blocked."
            else:
                user_error = "Security validation failed: Payload rejected by Immune System."
            return {"safe": False, "error": user_error}

        except SyntaxError as se:
            logger.error(f"Syntax validation failed: {se}")
            return {"safe": False, "error": f"SyntaxError: {str(se)}"}
        except Exception as e:  # noqa: BLE001
            logger.error(f"Unexpected error during static analysis: {e}")
            return {"safe": False, "error": f"AnalysisException: {str(e)}"}
