"""Application entry point."""

import asyncio
import logging

from app.bot.bot import setup_bot

# Version identifier for debugging
APP_VERSION = "1.2.0-production"


async def main() -> None:
    """Main application entry point."""
    bot, dp, container = await setup_bot()
    
    logger = logging.getLogger(__name__)
    logger.info(f"App version: {APP_VERSION}")

    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        await container.beget_manager.stop()
        await container.db.disconnect()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
