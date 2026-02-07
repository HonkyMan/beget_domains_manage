"""Bot commands registration.

Registers BotCommand menu with Telegram API so users can see
available commands in the interface.
"""

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault


async def register_bot_commands(bot: Bot, admin_chat_id: int) -> None:
    """Register bot commands with Telegram.
    
    Sets up two command scopes:
    1. Default commands visible to all users
    2. Admin commands visible only in admin chat
    
    Args:
        bot: The Bot instance
        admin_chat_id: Chat ID of the admin
    """
    # Commands for all users
    default_commands = [
        BotCommand(command="start", description="Main menu"),
        BotCommand(command="domains", description="Domain list"),
        BotCommand(command="help", description="Help & info"),
    ]
    
    # Additional commands for admin
    admin_commands = [
        BotCommand(command="start", description="Main menu"),
        BotCommand(command="domains", description="Domain list"),
        BotCommand(command="admin", description="Admin panel"),
        BotCommand(command="help", description="Help & info"),
    ]
    
    # Set default commands for all chats
    await bot.set_my_commands(
        commands=default_commands,
        scope=BotCommandScopeDefault(),
    )
    
    # Set admin commands for admin chat
    await bot.set_my_commands(
        commands=admin_commands,
        scope=BotCommandScopeChat(chat_id=admin_chat_id),
    )
