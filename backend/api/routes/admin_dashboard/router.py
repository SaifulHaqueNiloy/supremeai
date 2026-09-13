"""Combined ``/admin-api`` router for the admin dashboard package.

Replicates the original single-module ``APIRouter(...)`` configuration exactly
and aggregates the domain sub-routers (observability, costs, users, ops,
security, deployment, config, commandcenter).

Aggregation note: the sub-routers are constructed with the identical
prefix/tags/dependencies as the original monolithic router, so their route
objects already carry the baked-in ``/admin-api`` path prefix, the router-level
auth dependencies and the ``admin-dashboard`` OpenAPI tags — exactly like the
pre-refactor route objects. Their ``routes`` lists are appended directly
instead of ``include_router`` so that the combined router still exposes the
real ``APIRoute`` objects (route count, ``route.dependant`` auth-dep matrix
checks and route-matching order all behave exactly like the pre-refactor
monolith; FastAPI >= 0.141 would otherwise insert lazy ``_IncludedRouter``
wrapper objects).

Do NOT call ``include_router(sub_router)`` on the combined router — the
sub-router routes already contain the ``/admin-api`` prefix, so that would
double the prefix.
"""

from fastapi import APIRouter, Depends

from api.routes.admin_auth import admin_rate_limit, require_admin_token

from .commandcenter import router as commandcenter_router
from .config import router as config_router
from .costs import router as costs_router
from .deployment import router as deployment_router
from .observability import router as observability_router
from .ops import router as ops_router
from .security import router as security_router
from .users import router as users_router

router = APIRouter(
    prefix="/admin-api",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)

# Registration order mirrors the original monolith's endpoint order. Route
# matching is unaffected by the domain grouping (no two sub-routers register
# overlapping paths); the only duplicate-path pair (GET/POST /approvals,
# intentionally registered twice for backward compatibility) keeps its
# original relative order inside commandcenter.py.
router.routes.extend(observability_router.routes)
router.routes.extend(costs_router.routes)
router.routes.extend(users_router.routes)
router.routes.extend(ops_router.routes)
router.routes.extend(security_router.routes)
router.routes.extend(deployment_router.routes)
router.routes.extend(config_router.routes)
router.routes.extend(commandcenter_router.routes)
