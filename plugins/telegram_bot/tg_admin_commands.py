from telegram import Update, User
from telegram.ext import ContextTypes, CommandHandler, filters
from telegram.constants import ChatMemberStatus
from nonebot.log import logger

from .client import ptb_app
from .config import plugin_config
from .data_source import whitelist_manager

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the chat."""
    user = update.effective_user
    chat = update.effective_chat
    
    if not user or not chat:
        return False
        
    # Private chat: always allowed (assuming bot owner commands, but we need security)
    # Actually for now let's only allow this in the configured groups to avoid random people controlling it
    if chat.id not in plugin_config.telegram_forward_chat:
        return False
    return user.id == plugin_config.bot_owner

async def get_target_users(update: Update) -> list[User]:
    """Extract users from reply."""
    users = []
    msg = update.message
    
    # 1. Reply
    if msg.reply_to_message and msg.reply_to_message.from_user:
        users.append(msg.reply_to_message.from_user)
    
    return users

async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("权限不足")
        return

    targets = await get_target_users(update)
    if not targets:
        await update.message.reply_text("请回复某人或通过文本 @提及 用户")
        return

    added = []
    for user in targets:
        if user.is_bot:
            continue
        whitelist_manager.add(user.id)
        added.append(f"{user.full_name}")

    if added:
        await update.message.reply_text(f"✅ 已添加白名单: {', '.join(added)}")
    else:
        await update.message.reply_text("⚠️ 未找到有效用户或目标是机器人")

async def cmd_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ 权限不足")
        return

    targets = await get_target_users(update)
    if not targets:
        await update.message.reply_text("❌ 请回复某人或通过文本 @提及 用户")
        return

    removed = []
    for user in targets:
        whitelist_manager.remove(user.id)
        removed.append(f"{user.full_name}")

    if removed:
        await update.message.reply_text(f"🗑️ 已移除白名单: {', '.join(removed)}")

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    # This only shows IDs, showing names would require fetching them which is slow or caching
    # We will just show IDs for now
    ids = whitelist_manager.get_all()
    if not ids:
        await update.message.reply_text("📜 当前白名单为空 (所有人可用)")
    else:
        # Just count or show first few? Or all?
        await update.message.reply_text(f"📜 白名单包含 {len(ids)} 个 ID: {ids}")


# Register handlers
if ptb_app:
    # Commands: /add, /header, /permit ? specific naming
    # Using /allow and /ban for clarity
    ptb_app.add_handler(CommandHandler(["allow", "add"], cmd_add))
    ptb_app.add_handler(CommandHandler(["disallow", "ban", "del", "remove"], cmd_del))
    ptb_app.add_handler(CommandHandler(["whitelist", "list"], cmd_list))
