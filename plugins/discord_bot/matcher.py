from nonebot import on_message
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from .config import plugin_config

async def is_mygroup(event: GroupMessageEvent):
    return (event.self_id != event.sender.user_id) and (event.group_id in plugin_config.discord_forward_group)

async def not_banned(event: GroupMessageEvent):
    return event.sender.user_id not in plugin_config.discord_black_qq

forward_bot = on_message(rule=Rule(is_mygroup, not_banned))
