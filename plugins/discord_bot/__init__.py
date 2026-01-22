import asyncio
import nonebot
from nonebot import get_driver

from .config import plugin_config
from .client import client
# Import handlers to register them
from . import discord_handle
from . import onebot_handle

DRIVER = get_driver()

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
