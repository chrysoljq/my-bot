from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg
from .data_source import whitelist_manager

# Commands for managing whitelist
tg_add = on_command("tg_add", permission=SUPERUSER, priority=10, block=True)
tg_del = on_command("tg_del", permission=SUPERUSER, priority=10, block=True)
tg_list = on_command("tg_list", permission=SUPERUSER, priority=10, block=True)

@tg_add.handle()
async def handle_add(args: Message = CommandArg()):
    id_str = args.extract_plain_text().strip()
    if not id_str.isdigit():
        await tg_add.finish("请输入有效的 Telegram User ID")
        return
    
    uid = int(id_str)
    whitelist_manager.add(uid)
    await tg_add.finish(f"已添加 TG 用户 {uid} 到白名单")

@tg_del.handle()
async def handle_del(args: Message = CommandArg()):
    id_str = args.extract_plain_text().strip()
    if not id_str.isdigit():
        await tg_del.finish("请输入有效的 Telegram User ID")
        return

    uid = int(id_str)
    whitelist_manager.remove(uid)
    await tg_del.finish(f"已从白名单移除 TG 用户 {uid}")

@tg_list.handle()
async def handle_list():
    lst = whitelist_manager.get_all()
    if not lst:
        await tg_list.finish("当前白名单为空 (允许所有人)")
    else:
        await tg_list.finish(f"当前白名单用户: {lst}")
