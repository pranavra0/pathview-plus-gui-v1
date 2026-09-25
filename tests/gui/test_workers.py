from __future__ import annotations

import time

from pathview.gui.models import RenderConfig, RunResult
from pathview.gui.workers import RenderWorker


def test_worker_cancels_between_pathways(monkeypatch):
    calls: list[str] = []

    def fake_render(config, cancel):
        yield RunResult("first", status="success")
        if cancel():
            return
        yield RunResult("second", status="success")

    monkeypatch.setattr("pathview.gui.workers.render", fake_render)
    worker: RenderWorker
    worker = RenderWorker(
        RenderConfig(pathway_ids=["first", "second"]),
        on_result=lambda result: (calls.append(result.pathway_id), worker.cancel()),
    )
    done: list[bool] = []
    worker.on_done = lambda: done.append(True)
    worker.start()
    deadline = time.monotonic() + 2
    while worker.running and time.monotonic() < deadline:
        time.sleep(0.005)

    assert calls == ["first"]
    assert done == [True]
    assert worker.running is False
