"""Security module initialization.

This module provides centralized access to security components:
- Enhanced AST Scanner (ML-based code analysis)
- Behavioral Analyzer (anomaly detection)
- AutonoGuard Engine (JIT OTP, IP Churn, Self-healing)
"""

from __future__ import annotations

from typing import Any

from core.security.enhanced_ast_scanner import SecurityScanner, SecurityIssue
from core.security.behavioral_analyzer import BehavioralAnalyzer, AnomalyAlert, get_analyzer

# Version info
__version__ = "2.0.0"

# Export main classes
__all__ = [
    # Scanner
    "SecurityScanner",
    "SecurityIssue",
    # Behavioral Analysis
    "BehavioralAnalyzer",
    "AnomalyAlert",
    "get_analyzer",
]


# Global instances
_security_scanner: SecurityScanner | None = None
_behavioral_analyzer: BehavioralAnalyzer | None = None


def get_security_scanner() -> SecurityScanner:
    """Get or create global security scanner instance.

    Returns:
        SecurityScanner instance
    """
    global _security_scanner
    if _security_scanner is None:
        _security_scanner = SecurityScanner()
    return _security_scanner


def get_behavioral_analyzer() -> BehavioralAnalyzer:
    """Get or create global behavioral analyzer instance.

    Returns:
        BehavioralAnalyzer instance
    """
    global _behavioral_analyzer
    if _behavioral_analyzer is None:
        _behavioral_analyzer = BehavioralAnalyzer()
    return _behavioral_analyzer


def scan_codebase(paths: list[str] | None = None) -> dict[str, Any]:
    """Scan codebase for security issues.

    Args:
        paths: List of paths to scan

    Returns:
        Security scan report
    """
    scanner = get_security_scanner()

    if paths:
        scanner.scan_paths = paths

    issues = scanner.scan_all()
    return scanner.generate_report(issues)


def record_user_behavior(
    user_id: str,
    ip_address: str,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record user behavior event for anomaly detection.

    Args:
        user_id: User identifier
        ip_address: IP address
        action: Action performed
        metadata: Additional metadata
    """
    analyzer = get_behavioral_analyzer()
    analyzer.record_event(user_id, ip_address, action, metadata)


def get_user_risk_score(user_id: str) -> float:
    """Calculate risk score for a user.

    Args:
        user_id: User identifier

    Returns:
        Risk score between 0.0 and 1.0
    """
    analyzer = get_behavioral_analyzer()
    return analyzer.get_user_risk_score(user_id)


# Convenience function for CLI
def run_security_scan() -> int:
    """Run security scan from command line.

    Returns:
        Exit code (0 = success, 1 = critical issues found)
    """
    import sys

    try:
        report = scan_codebase()

        # Print summary
        print("\n🔒 Security Scan Results")
        print("=" * 50)
        print(f"Total Issues: {report['total_issues']}")
        print("\nBy Severity:")
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = report["by_severity"].get(severity, 0)
            print(f"  {severity.upper()}: {count}")

        print("\nBy Category:")
        for category, count in sorted(report["by_category"].items()):
            print(f"  {category}: {count}")

        # Show critical/high issues
        if report["by_severity"]["critical"] > 0 or report["by_severity"]["high"] > 0:
            print("\n⚠️  Critical/High Issues:")
            for issue in report["issues"]:
                if issue["severity"] in ["critical", "high"]:
                    print(f"\n  [{issue['severity'].upper()}] {issue['category']}")
                    print(f"    {issue['file']}:{issue['line']}")
                    print(f"    {issue['description']}")
                    print(f"    → {issue['recommendation']}")

        # Return non-zero exit code for CI/CD
        if report["by_severity"]["critical"] > 0 or report["by_severity"]["high"] > 0:
            return 1

        return 0

    except Exception as exc:
        print(f"❌ Security scan failed: {exc}", file=sys.stderr)
        return 1
