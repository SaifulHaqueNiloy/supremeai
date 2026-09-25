"""Tests for core/ast_security_scanner.py — AST-based security scanner."""
import pytest
from core.ast_security_scanner import AstSecurityScanner


class TestAstSecurityScanner:
    def test_init(self):
        scanner = AstSecurityScanner()
        assert scanner is not None

    def test_scan_safe_code(self):
        scanner = AstSecurityScanner()
        issues = scanner.scan("x = 1 + 1")
        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_scan_eval_usage(self):
        scanner = AstSecurityScanner()
        issues = scanner.scan("eval('1+1')")
        assert isinstance(issues, list)
        assert len(issues) > 0

    def test_scan_exec_usage(self):
        scanner = AstSecurityScanner()
        issues = scanner.scan("exec('import os')")
        assert len(issues) > 0

    def test_scan_subprocess_usage(self):
        scanner = AstSecurityScanner()
        issues = scanner.scan("import subprocess; subprocess.call('ls')")
        assert len(issues) > 0

    def test_scan_empty_code(self):
        scanner = AstSecurityScanner()
        issues = scanner.scan("")
        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_scan_import_os(self):
        scanner = AstSecurityScanner()
        issues = scanner.scan("import os")
        assert isinstance(issues, list)

    def test_scan_hardcoded_secret(self):
        scanner = AstSecurityScanner()
        issues = scanner.scan('API_KEY = "sk-1234567890abcdef"')
        assert isinstance(issues, list)
