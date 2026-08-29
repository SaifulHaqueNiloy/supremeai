import sys
import time

F = open("probe_out.txt", "w")


def log(msg):
    F.write(msg + "\n")
    F.flush()


log("start")
for mod in [
    "core.env_validator",
    "core.cache",
    "core.intelligent_cache",
    "core.db",
    "core.output_validator",
    "core.retry_handler",
    "core.embeddings",
    "core.automation.idempotency",
    "core.cache_manager",
]:
    t = time.time()
    try:
        __import__(mod)
        log("import %s OK %ss" % (mod, round(time.time() - t, 2)))
    except Exception as e:
        log("import %s ERR %r" % (mod, e))

F.close()
log("done")
