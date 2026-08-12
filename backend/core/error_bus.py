# DEPRECATED: backend.core.error_bus -> backend.core.errors.error_bus
# নোট: backend architecture refactor plan অনুযায়ী সরানো হয়েছে।
# ভবিষ্যতে সব importer নতুন path-এ সরিয়ে এই shim মুছে ফেলতে হবে।
import importlib
import warnings

_DEPRECATED_TARGET = "backend.core.errors.error_bus"
_warned = False

def __getattr__(name):
    global _warned
    if not _warned:
        warnings.warn(
            "backend.core.error_bus is deprecated; import from backend.core.errors.error_bus",
            DeprecationWarning, stacklevel=2,
        )
        _warned = True
    mod = importlib.import_module(_DEPRECATED_TARGET)
    return getattr(mod, name)

def __dir__():
    return list(importlib.import_module(_DEPRECATED_TARGET).__dict__.keys())
