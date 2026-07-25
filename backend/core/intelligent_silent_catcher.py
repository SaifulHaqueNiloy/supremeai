import sys
import logging
import traceback

from core.messaging.event_bus import error_event_bus, ErrorEvent, ErrorContext

logger = logging.getLogger("supremeai.silent_catcher")


def intelligent_excepthook(exc_type, exc_value, exc_traceback):
    """
    বাংলা মন্তব্য: Runtime hook for catching silent or unhandled exceptions.
    It guarantees that an ErrorEvent is emitted to the IntelligentErrorBus.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Extract useful information
    tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
    full_traceback = "".join(tb_list)

    # Try to find the originating module
    module = "unknown"
    if exc_traceback:
        frame = exc_traceback
        while frame.tb_next:
            frame = frame.tb_next
        module = frame.tb_frame.f_globals.get("__name__", "unknown")

    logger.critical(f"[SilentCatcher] Unhandled exception in {module}: {exc_value}")

    # Forcibly emit to the bus
    event = ErrorEvent(
        module=module,
        error_type="SILENT_FAILURE_DETECTED",
        message=f"Unhandled {exc_type.__name__}: {exc_value}",
        severity="CRITICAL",
        context={"traceback": full_traceback},
        structured_context=ErrorContext(module=module, env="production"),
    )

    # Emit synchronously since we are in a crash state
    error_event_bus.emit(event)

    # Call the original excepthook to preserve default behavior (like printing to stderr)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def setup_silent_catcher():
    """
    বাংলা মন্তব্য: Initialize the global exception hook.
    Must be called early in the application lifecycle.
    """
    sys.excepthook = intelligent_excepthook

    # Thread target wrapper to catch silent thread crashes
    def thread_target_wrapper(target):
        def wrapper(*args, **kwargs):
            try:
                return target(*args, **kwargs)
            except Exception as e:
                # If a thread crashes silently, it will now be caught
                intelligent_excepthook(type(e), e, e.__traceback__)

        return wrapper

    # Patch threading to use the wrapper
    import threading

    original_thread_init = threading.Thread.__init__

    def patched_thread_init(self, *args, **kwargs):
        original_thread_init(self, *args, **kwargs)
        if hasattr(self, "_target") and self._target is not None:
            self._target = thread_target_wrapper(self._target)

    threading.Thread.__init__ = patched_thread_init

    logger.info("[SilentCatcher] Global exception and thread hooks initialized.")
