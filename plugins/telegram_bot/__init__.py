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
from . import admin # Import OneBot admin commands (status)
from plugins.datastore import db

driver = get_driver()

@driver.on_startup
async def init_schema():
    await db.execute_script("""
    CREATE TABLE IF NOT EXISTS tg_msg_map (
        tg_id INTEGER NOT NULL,
        qq_id INTEGER NOT NULL,
        group_index INTEGER NOT NULL,
        timestamp INTEGER DEFAULT (strftime('%s', 'now')),
        PRIMARY KEY (tg_id, group_index)
    );
    CREATE INDEX IF NOT EXISTS idx_tg_qq_map ON tg_msg_map (qq_id, group_index);
    """)

@driver.on_bot_connect
async def start_tg():
    if not ptb_app:
        logger.warning("Telegram config missing, skipping.")
        return
    
    # Avoid re-initializing if already running (though PTB guards this usually)
    if ptb_app.running:
        logger.warning("Telegram Bot is already running, skipping start.")
        return

    logger.info("Starting Telegram Bot...")
    if not ptb_app._initialized:
        await ptb_app.initialize()
    
    await ptb_app.start()
    
    # In PTB v20+, updater.start_polling() is async and starts the polling loop in background task
    if not ptb_app.updater.running:
        await ptb_app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("Telegram Bot Started")

@driver.on_bot_disconnect
async def stop_tg():
    if ptb_app:
        logger.info("Pausing Telegram Bot (OneBot disconnected)...")
        # Only stop polling and the application loop, do NOT shutdown.
        # Shutdown is terminal and prevents restart.
        if ptb_app.updater.running:
            await ptb_app.updater.stop()
        if ptb_app.running:
            await ptb_app.stop()
        logger.info("Telegram Bot Paused")

@driver.on_shutdown
async def shutdown_tg():
    """True shutdown when the entire process is exiting"""
    if ptb_app:
        logger.info("Shutting down Telegram Bot...")
        try:
            if ptb_app.updater.running:
                await ptb_app.updater.stop()
            if ptb_app.running:
                await ptb_app.stop()
            await ptb_app.shutdown()
        except Exception as e:
            logger.warning(f"Error during Telegram Bot shutdown (ignored): {e}")
        logger.info("Telegram Bot Shutdown Complete")
