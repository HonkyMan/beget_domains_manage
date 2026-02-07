"""Bot initialization and setup."""

import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.config import get_settings
from app.core.container import DependencyContainer
from app.core.middleware import DependencyMiddleware
from app.services.database import Database, ChatsRepository, LogsRepository, PermissionsRepository
from app.services.beget import BegetClientManager
from app.services.permissions import PermissionChecker
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.middlewares.logging import LoggingMiddleware
from app.bot.keyboards.common import main_menu_keyboard
from app.bot.commands import register_bot_commands
from app.bot.callback_data import CB_MENU_MAIN, CB_CANCEL
from app.modules.admin.router import router as admin_router, setup_admin_deps
from app.modules.domains.router import router as domains_router


# Base handlers router
base_router = Router(name="base")


@base_router.message(F.text == "/start")
async def cmd_start(message: Message, is_admin: bool = False) -> None:
    """Handle /start command."""
    await message.answer(
        "Welcome to Beget Manager!\n\n"
        "Use the menu below to manage domains and DNS records.",
        reply_markup=main_menu_keyboard(is_admin),
    )


@base_router.message(F.text == "/help")
async def cmd_help(message: Message, is_admin: bool = False) -> None:
    """Handle /help command."""
    help_text = (
        "Beget Manager Bot\n\n"
        "Commands:\n"
        "/start - Main menu\n"
        "/domains - View domain list\n"
        "/help - This help message\n"
    )
    
    if is_admin:
        help_text += "/admin - Admin panel\n"
    
    help_text += (
        "\nFeatures:\n"
        "- Browse domains and subdomains\n"
        "- Manage DNS records (A, TXT)\n"
        "- Create and delete subdomains\n"
    )
    
    if is_admin:
        help_text += (
            "\nAdmin features:\n"
            "- Manage allowed chats\n"
            "- Configure permissions\n"
            "- View action logs\n"
        )
    
    await message.answer(help_text, reply_markup=main_menu_keyboard(is_admin))


@base_router.message(F.text == "/domains")
async def cmd_domains(
    message: Message,
    container: DependencyContainer,
    user_chat_id: int,
    is_admin: bool = False,
) -> None:
    """Handle /domains command - quick access to domain list."""
    from app.services.beget import DomainsService
    from app.modules.domains.domain.keyboards import domains_list_keyboard
    
    try:
        async with container.beget_manager.client() as client:
            domains_service = DomainsService(client)
            all_domains = await domains_service.get_domains()
    except Exception as e:
        await message.answer(f"Error loading domains: {e}")
        return

    # Filter domains by user permissions
    domains = await container.permission_checker.filter_domains(user_chat_id, all_domains)

    if not domains:
        await message.answer(
            "No domains available.\n\n"
            "Contact administrator to get access to domains."
        )
        return

    await message.answer(
        "Select a domain:",
        reply_markup=domains_list_keyboard(domains),
    )


@base_router.message(F.text == "/admin")
async def cmd_admin(message: Message, is_admin: bool = False) -> None:
    """Handle /admin command."""
    if not is_admin:
        await message.answer("This command is only available for administrators.")
        return
    
    from app.modules.admin.router import admin_menu_keyboard
    await message.answer(
        "Admin Panel\n\nSelect an option:",
        reply_markup=admin_menu_keyboard(),
    )


@base_router.callback_query(F.data == CB_MENU_MAIN)
async def main_menu(callback: CallbackQuery, is_admin: bool = False) -> None:
    """Show main menu."""
    await callback.message.edit_text(
        "Main Menu\n\nSelect an action:",
        reply_markup=main_menu_keyboard(is_admin),
    )
    await callback.answer()


@base_router.callback_query(F.data == CB_CANCEL)
async def cancel_action(
    callback: CallbackQuery, 
    state: FSMContext, 
    is_admin: bool = False
) -> None:
    """Cancel current action and return to main menu."""
    await state.clear()
    await callback.message.edit_text(
        "Action cancelled.\n\nMain Menu:",
        reply_markup=main_menu_keyboard(is_admin),
    )
    await callback.answer()


async def setup_bot() -> tuple[Bot, Dispatcher, DependencyContainer]:
    """Setup and configure bot with dependency injection."""
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize database
    db = Database(settings.db_path)
    await db.connect()

    # Create repositories
    chats_repo = ChatsRepository(db)
    logs_repo = LogsRepository(db)
    permissions_repo = PermissionsRepository(db)

    # Create permission checker
    permission_checker = PermissionChecker(permissions_repo, settings.admin_chat_id)

    # Create Beget client manager
    beget_manager = BegetClientManager(
        login=settings.beget_login,
        password=settings.beget_password,
    )
    await beget_manager.start()

    # Build dependency container
    container = DependencyContainer(
        settings=settings,
        db=db,
        chats_repo=chats_repo,
        logs_repo=logs_repo,
        permissions_repo=permissions_repo,
        permission_checker=permission_checker,
        beget_manager=beget_manager,
        admin_chat_id=settings.admin_chat_id,
    )

    # Setup module dependencies (for backward compatibility during migration)
    setup_admin_deps(chats_repo, logs_repo, permissions_repo, settings.admin_chat_id)

    # Initialize bot and dispatcher
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Register middlewares
    # 1. Dependency injection middleware (adds container to all handlers)
    dp.message.middleware(DependencyMiddleware(container))
    dp.callback_query.middleware(DependencyMiddleware(container))
    
    # 2. Auth middleware (checks if user is allowed)
    auth_middleware = AuthMiddleware(chats_repo, permissions_repo, settings.admin_chat_id)
    dp.message.middleware(auth_middleware)
    dp.callback_query.middleware(auth_middleware)
    
    # 3. Logging middleware
    dp.message.middleware(LoggingMiddleware(logs_repo, bot, settings.admin_chat_id))
    dp.callback_query.middleware(LoggingMiddleware(logs_repo, bot, settings.admin_chat_id))

    # Register routers
    dp.include_router(base_router)
    dp.include_router(admin_router)
    dp.include_router(domains_router)

    # Register bot commands menu
    await register_bot_commands(bot, settings.admin_chat_id)

    return bot, dp, container
