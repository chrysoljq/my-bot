import asyncio
import nonebot
from nonebot import get_driver

from .config import plugin_config
from .client import client
# Import handlers to register them
from . import discord_handle
from . import onebot_handle
from plugins.datastore import db

DRIVER = get_driver()

@DRIVER.on_startup
async def init_schema():
    await db.execute_script("""
    CREATE TABLE IF NOT EXISTS discord_msg_map (
        discord_id INTEGER NOT NULL,
        qq_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL,
        timestamp INTEGER DEFAULT (strftime('%s', 'now')),
        PRIMARY KEY (discord_id, channel_id)
    );
    CREATE INDEX IF NOT EXISTS idx_dc_qq_map ON discord_msg_map (qq_id, channel_id);
    """)

@DRIVER.on_bot_connect
async def main():
    if not plugin_config.discord_token:
        nonebot.logger.warning("Discord token not set, skipping start.")
        return
        
    if not client.is_ready():
        # Start discord client in background
        asyncio.create_task(client.start(plugin_config.discord_token, reconnect=True))

@DRIVER.on_bot_disconnect
async def stop():
    await client.close()
