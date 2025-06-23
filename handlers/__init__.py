from .accounts import router as accounts_router
from .budgets import router as budgets_router
from .categories import router as categories_router
from .goals import router as goals_router
from .recurring import router as recurring_router
from .start import router as start_router
from .tags import router as tags_router
from .transactions import router as transactions_router


list_of_routers = [
    start_router,
    accounts_router,
    budgets_router,
    categories_router,
    goals_router,
    recurring_router,
    tags_router,
    transactions_router,
]
