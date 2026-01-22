from nonebot import on_message
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from .config import plugin_config

async def is_forward_group(event: GroupMessageEvent):
    return (event.self_id != event.sender.user_id) and (event.group_id in plugin_config.telegram_forward_group)

# Simple rule, extend if needed (blacklist etc)
forward_bot = on_message(rule=Rule(is_forward_group))
