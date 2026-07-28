"""
Root tools package initialization.

This package contains various specialized tools for different purposes.
"""

# Import the backend tools to maintain compatibility
try:
    from backend.tools import *
except ImportError:
    # If backend tools are not available, define basic structure
    pass

# মডিউল এক্সপোর্ট লিস্ট টাইপ অ্যানোটেশন সহ
__all__: list[str] = []

