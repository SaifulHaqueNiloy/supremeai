import importlib

mod = importlib.import_module("core.logging")
print("FILE:", getattr(mod, "__file__", "NO FILE"))
print("GETATTR SomeExport:", mod.SomeExport if hasattr(mod, "SomeExport") else "MISSING")
