"""Application entry point."""

import asyncio
import logging

from app.bot.bot import setup_bot


async def main() -> None:
    """Main application entry point."""
    bot, dp, container = await setup_bot()
    
    logger = logging.getLogger(__name__)

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
