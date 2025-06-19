from aiogram import Router
from handlers.main_menu import router as main_menu_router
from handlers.task_creation import router as task_creation_router
from handlers.category_management import router as category_management_router
from handlers.task_view import router as task_view_router
from handlers.cancel_handler import router as cancel_handler_router

router = Router()

router.include_router(main_menu_router)
router.include_router(task_creation_router)
router.include_router(category_management_router)
router.include_router(task_view_router)
router.include_router(cancel_handler_router)