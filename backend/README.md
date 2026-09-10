# SupremeAI Backend

> **Note:** The backend architecture, deployment, and configuration instructions have been consolidated into the root repository. 
>
> Please refer to the [Root README](../../README.md) for the current production architecture (Render + PostgreSQL/Supabase).
>
> Legacy deployment instructions (e.g., Google Cloud Run) have been moved to `docs/archive/legacy_cloud_run_deployment.md`.

## Worker health and task boundaries

The worker exposes separate operational signals: `/health/live` confirms only that the process is running, `/health/ready` confirms that the configured queue is available for work, and `/health/degraded` reports partial dependency failure without pretending the worker is ready. Task submissions must include a tenant identifier; unsupported capabilities and oversized metadata are rejected at the boundary.

The worker uses `core.queue.task_queue_enhanced` as its application queue boundary. Celery is an execution process/supervisor where configured, not a second source of task contracts or policy. Free-tier keep-alive pings are best-effort only and do not provide uptime, capacity, or fault-tolerance guarantees.
