import sys
import time


def test_import(module_name):
    print(f"Importing {module_name}...")
    start = time.time()
    try:
        __import__(module_name)
        print(f"  -> Done in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"  -> Failed: {e}")


test_import("core.app")
test_import("api.routers")
