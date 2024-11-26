from .admin.admin_router import admin_router
from .channels_requests_handler import join_requests_router
from .start.start_router import start_router
from .not_subscribed.check_sub_router import check_sub_router
from .user_logic.user_handler import user_router

routers = [
    start_router,
    user_router,
    admin_router,
    check_sub_router,
    join_requests_router,
]

