import discord
from .config import plugin_config

intents = discord.Intents.default()
intents.message_content = True

# proxy handling if needed
proxy_url = plugin_config.discord_proxy

client = discord.Client(intents=intents, proxy=proxy_url)
