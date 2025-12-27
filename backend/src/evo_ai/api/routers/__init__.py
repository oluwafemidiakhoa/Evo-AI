"""API routers."""

from evo_ai.api.routers.campaigns import router as campaigns_router
from evo_ai.api.routers.rounds import router as rounds_router
from evo_ai.api.routers.variants import router as variants_router
from evo_ai.api.routers.evaluations import router as evaluations_router
from evo_ai.api.routers.reports import router as reports_router
from evo_ai.api.routers.tasks import router as tasks_router

__all__ = [
    "campaigns_router",
    "rounds_router",
    "variants_router",
    "evaluations_router",
    "reports_router",
    "tasks_router",
]
