"""Detector exports + registry."""
from __future__ import annotations

from typing import Type

from pyerrorfix.detectors.base import BaseDetector
from pyerrorfix.detectors.syntax import SyntaxDetector
from pyerrorfix.detectors.core_python import CorePythonDetector
from pyerrorfix.detectors.imports import ImportDetector
from pyerrorfix.detectors.files import FileDetector
from pyerrorfix.detectors.asyncio_err import AsyncioDetector
from pyerrorfix.detectors.database import DatabaseDetector
from pyerrorfix.detectors.web_api import WebApiDetector
from pyerrorfix.detectors.concurrency import ConcurrencyDetector
from pyerrorfix.detectors.typing_err import TypingDetector
from pyerrorfix.detectors.security import SecurityDetector
from pyerrorfix.detectors.resources import ResourceDetector
from pyerrorfix.detectors.deprecation import DeprecationDetector
from pyerrorfix.detectors.logging_err import LoggingDetector
# NEW detectors for the expanded 11-category taxonomy:
from pyerrorfix.detectors.network_io import NetworkIoDetector
from pyerrorfix.detectors.linter_quality import LinterQualityDetector
from pyerrorfix.detectors.auth_security import AuthSecurityDetector
from pyerrorfix.detectors.testing import TestingDetector
from pyerrorfix.detectors.infra_deploy import InfraDeployDetector

ALL_DETECTORS: list[Type[BaseDetector]] = [
    SyntaxDetector,
    CorePythonDetector,
    ImportDetector,
    FileDetector,
    AsyncioDetector,
    DatabaseDetector,
    WebApiDetector,
    ConcurrencyDetector,
    TypingDetector,
    SecurityDetector,
    ResourceDetector,
    DeprecationDetector,
    LoggingDetector,
    # NEW
    NetworkIoDetector,
    LinterQualityDetector,
    AuthSecurityDetector,
    TestingDetector,
    InfraDeployDetector,
]

__all__ = ["ALL_DETECTORS", "BaseDetector"]

