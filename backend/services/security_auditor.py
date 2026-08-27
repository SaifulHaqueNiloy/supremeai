# DEPRECATED: backend.services.security_auditor -> backend.core.security.audit.security_auditor
# নোট: duplicate_detector.py file_level scan-এ ধরা পড়েছে যে এই ফাইলটি
# backend/core/security/audit/security_auditor.py-এর সাথে বাইট-ফর-বাইট
# অভিন্ন (778 লাইন), এবং কোনো importer কোনোটাকেই ব্যবহার করছে না — অর্থাৎ
# orphaned duplicate। core/security/audit/ path-টা প্রজেক্টের security মডিউল
# organization-এর সাথে সামঞ্জস্যপূর্ণ, তাই সেটাকে canonical রাখা হলো এবং এই
# ফাইলটাকে backward-compat shim বানানো হলো (idempotency_middleware.py-তে
# ব্যবহৃত একই প্যাটার্ন অনুসরণ করে)।
import importlib
import warnings

_DEPRECATED_TARGET = "core.security.audit.security_auditor"
_warned = False


def __getattr__(name):
    global _warned
    if not _warned:
        warnings.warn(
            "backend.services.security_auditor is deprecated; import from core.security.audit.security_auditor",
            DeprecationWarning,
            stacklevel=2,
        )
        _warned = True
    mod = importlib.import_module(_DEPRECATED_TARGET)
    return getattr(mod, name)


def __dir__():
    return list(importlib.import_module(_DEPRECATED_TARGET).__dict__.keys())
