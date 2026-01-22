import asyncio
from nonebot import get_driver, logger
from telegram import Update
from .client import ptb_app
from .config import plugin_config
import sys

# Import side-effects (handlers)
from . import telegram_handle
from . import onebot_handle
from . import commands # Import commands so they are registered OneBot commands
from . import tg_admin_commands # Import TG admin commands

driver = get_driver()

@driver.on_bot_connect
async def start_tg():
    if not ptb_app:
        logger.warning("Telegram config missing, skipping.")
        return
    
    logger.info("Starting Telegram Bot...")
    await ptb_app.initialize()
    await ptb_app.start()
    
    # In PTB v20+, updater.start_polling() is async and starts the polling loop in background task
    await ptb_app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram Bot Started")

@driver.on_bot_disconnect
async def stop_tg():
    if ptb_app:
        logger.info("Stopping Telegram Bot...")
        await ptb_app.updater.stop()
        await ptb_app.stop()
        await ptb_app.shutdown()
