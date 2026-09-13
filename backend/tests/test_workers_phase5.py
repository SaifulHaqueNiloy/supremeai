import pytest

from workers.precognitive_watcher import PrecognitiveWatcher
from workers.synaptic_dream import SynapticDreamWorker


@pytest.mark.asyncio
async def test_synaptic_dream_worker_cycle():
    worker = SynapticDreamWorker()
    report = await worker.execute_dream_cycle(tenant_id="test_tenant", retention_days=14)
    assert report.status == "completed"
    assert report.duration_ms >= 0.0
    assert isinstance(report.pruned_count, int)
    assert isinstance(report.consolidated_count, int)


@pytest.mark.asyncio
async def test_precognitive_watcher_scan():
    watcher = PrecognitiveWatcher()
    alerts = await watcher.scan_system_health()
    assert isinstance(alerts, list)
    active_alerts = watcher.get_active_alerts()
    assert isinstance(active_alerts, list)
