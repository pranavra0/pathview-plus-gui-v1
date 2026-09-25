"""Single-render worker with cooperative cancellation semantics."""

from __future__ import annotations

import threading
from collections.abc import Callable

from .models import RenderConfig, RunResult
from .services.render_service import RenderService, render

_default_render = render
try:
    from PySide6.QtCore import QObject, Signal

    _QT = True
except ImportError:
    _QT = False


if _QT:

    class RenderWorker(QObject):
        started = Signal()
        pathway_started = Signal(int, int, str)
        pathway_finished = Signal(object)
        pathway_failed = Signal(str, object)
        progress = Signal(int, int)
        finished = Signal()
        cancelled = Signal()

        def __init__(self, config: RenderConfig, on_result=None, on_done=None, parent=None):
            super().__init__(parent)
            self.config = config.copy()
            self.on_result = on_result
            self.on_done = on_done
            self._cancel = threading.Event()
            self._thread = None

        @property
        def running(self):
            return bool(self._thread and self._thread.is_alive())

        def cancel(self):
            self._cancel.set()

        def start(self):
            if self.running:
                raise RuntimeError("A render is already running")
            self._cancel.clear()

            def run():
                self.started.emit()
                cancelled_emitted = False
                try:

                    def on_started(index, total, pathway):
                        self.pathway_started.emit(index, total, pathway)
                        self.progress.emit(index, total)

                    if render is _default_render:
                        results = RenderService().render_batch(
                            self.config,
                            cancel=self._cancel.is_set,
                            on_started=on_started,
                        )
                    else:
                        results = render(self.config, self._cancel.is_set)
                    for result in results:
                        if result.status == "cancelled":
                            if not cancelled_emitted:
                                self.cancelled.emit()
                                cancelled_emitted = True
                        elif result.status == "success":
                            self.pathway_finished.emit(result)
                        else:
                            self.pathway_failed.emit(
                                result.pathway, result.error or "Render failed"
                            )
                        if self.on_result:
                            self.on_result(result)
                except Exception as exc:
                    self.pathway_failed.emit("", f"{type(exc).__name__}: {exc}")
                finally:
                    if self._cancel.is_set() and not cancelled_emitted:
                        self.cancelled.emit()
                    self.finished.emit()
                    if self.on_done:
                        self.on_done()

            self._thread = threading.Thread(target=run, name="pathview-render", daemon=True)
            self._thread.start()
else:

    class RenderWorker:
        def __init__(
            self,
            config: RenderConfig,
            on_result: Callable[[RunResult], None] | None = None,
            on_done: Callable[[], None] | None = None,
        ):
            self.config = config.copy()
            self.on_result = on_result
            self.on_done = on_done
            self._cancel = threading.Event()
            self._thread = None

        @property
        def running(self):
            return bool(self._thread and self._thread.is_alive())

        def cancel(self):
            self._cancel.set()

        def start(self):
            if self.running:
                raise RuntimeError("A render is already running")

            def run():
                try:
                    for item in render(self.config, self._cancel.is_set):
                        if self.on_result:
                            self.on_result(item)
                finally:
                    if self.on_done:
                        self.on_done()

            self._thread = threading.Thread(target=run, name="pathview-render", daemon=True)
            self._thread.start()
