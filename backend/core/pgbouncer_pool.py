# DEPRECATED: backend.core.pgbouncer_pool -> backend.database.pgbouncer_pool
# নোট: backend architecture refactor plan অনুযায়ী সরানো হয়েছে।
# ভবিষ্যতে সব importer নতুন path-এ সরিয়ে এই shim মুছে ফেলতে হবে।
import importlib
import warnings

_DEPRECATED_TARGET = "database.pgbouncer_pool"
_warned = False

def _get_target_module():
    try:
        return importlib.import_module(_DEPRECATED_TARGET)
    except ModuleNotFoundError:
        return importlib.import_module(f"backend.{_DEPRECATED_TARGET}")

def __getattr__(name):
    global _warned
    if not _warned:
        warnings.warn(
            "backend.core.pgbouncer_pool is deprecated; import from database.pgbouncer_pool",
            DeprecationWarning, stacklevel=2,
        )
        _warned = True
    mod = _get_target_module()
    return getattr(mod, name)

def __dir__():
    return list(_get_target_module().__dict__.keys())
