from fastapi import APIRouter

from core.zero_cost_architecture.zero_cost_patch_phase1_4 import (
    get_orchestrator,
    get_zero_cost_config,
)

router = APIRouter(prefix="/zero-cost", tags=["Zero-Cost Architecture"])


@router.get("/health")
async def zero_cost_health():
    orchestrator = get_orchestrator()
    return {
        "status": "healthy",
        "queue": orchestrator.queue.get_metrics(),
        "redis_connected": orchestrator.redis.is_connected,
        "config": {
            "max_concurrent": get_zero_cost_config().ZERO_COST_MAX_CONCURRENT,
            "timeout": get_zero_cost_config().ZERO_COST_TASK_TIMEOUT,
            "self_healing": get_zero_cost_config().SELF_HEALING,
        },
    }


@router.get("/metrics")
async def zero_cost_metrics():
    orchestrator = get_orchestrator()
    cb_metrics = {name: cb.get_metrics() for name, cb in orchestrator.circuit_breakers.items()}
    return {
        "queue_metrics": orchestrator.queue.get_metrics(),
        "circuit_breakers": cb_metrics,
        "learning_metrics": orchestrator.learning_engine.get_learning_metrics(),
    }


@router.get("/recommendations")
async def zero_cost_recommendations():
    orchestrator = get_orchestrator()
    metrics = orchestrator.learning_engine.get_learning_metrics()

    recommendations = []
    for op, param in metrics.items():
        if param.get("p95_duration", 0) > get_zero_cost_config().ZERO_COST_TASK_TIMEOUT * 0.8:
            recommendations.append(
                f"Timeout for {op} is approaching P95 duration. Consider increasing it."
            )
        if param.get("error_rate", 0) > 0.1:
            recommendations.append(
                f"High error rate ({param['error_rate'] * 100:.1f}%) observed for {op}."
            )

    if not recommendations:
        recommendations.append("System is running optimally within Zero-Cost constraints.")

    return {"recommendations": recommendations}
