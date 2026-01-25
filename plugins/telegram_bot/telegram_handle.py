import nonebot
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, MessageHandler, filters

from .client import ptb_app
from .config import plugin_config
from plugins.datastore import db
from .data_source import whitelist_manager

async def tg_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.channel_post
    if not msg:
        return
    chat_id = msg.chat.id
    if chat_id not in plugin_config.telegram_forward_chat:
        return

    # Check Whitelist
    user_id = msg.from_user.id if msg.from_user else 0
    if not whitelist_manager.is_allowed(user_id):
        # Optional: Log or ignore
        return

    # Find matching index for Chat ID AND Topic ID
    thread_id = msg.message_thread_id if msg.is_topic_message else 0
    
    indx = -1
    for i, cid in enumerate(plugin_config.telegram_forward_chat):
        if cid == chat_id:
            # Check topic
            # Get configured topic or 0 if index out of bounds or None
            # Assuming list might be shorter or contain 0/None
            cfg_topic = 0
            if i < len(plugin_config.telegram_forward_topic):
                cfg_topic = plugin_config.telegram_forward_topic[i] or 0
            
            msg_topic = thread_id or 0
            
            if cfg_topic == msg_topic:
                indx = i
                break
    
    if indx == -1:
        # No exact match found (e.g. strict topic matching), ignore or fallback?
        # If user defined specific topics, we should ignore mismatched messages.
        return

    group_id = plugin_config.telegram_forward_group[indx]

    # Content processing
    user_name = msg.from_user.full_name if msg.from_user else msg.chat.title or "Unknown"
    
    # Text
    content = ""
    if msg.text:
        content = msg.text
    elif msg.caption:
        content = msg.caption

    # Prefix
    qq_msg = f"<tg>({user_name}): {content}"

    # Handle Media
    # Photos
    if msg.photo:
        # Get largest photo
        photo = msg.photo[-1]
        file_obj = await photo.get_file()
        url = file_obj.file_path
        qq_msg += f"[CQ:image,file={url}]"

    # Stickers
    if msg.sticker:
        from .sticker import get_sticker_cq
        cq_code = await get_sticker_cq(msg.sticker)
        qq_msg += cq_code

    # Handle Reply
    if msg.reply_to_message:
        reply_id = msg.reply_to_message.message_id
        # Check database for mapping
        row = await db.fetchone(
            "SELECT qq_id FROM tg_msg_map WHERE tg_id = ? AND group_index = ?", 
            (reply_id, indx)
        )
        if row:
            qq_id = row['qq_id']
            qq_msg = f"[CQ:reply,id={qq_id}] " + qq_msg

    # Send to OneBot
    try:
        bot: Bot = nonebot.get_bot()
        result = await bot.send_group_msg(group_id=group_id, message=qq_msg)
        
        # Record mapping
        if result and 'message_id' in result:
            qq_msg_id = result['message_id']
            # Save to DB
            await db.execute(
                "INSERT INTO tg_msg_map (tg_id, qq_id, group_index) VALUES (?, ?, ?)",
                (msg.message_id, qq_msg_id, indx)
            )
             
    except Exception as e:
        logger.error(f"Failed to bridge TG -> QQ: {e}")

# Register handler
if ptb_app:
    # Filter for monitored chats only
    chat_filter = filters.Chat(chat_id=plugin_config.telegram_forward_chat)
    # Using generic ALL types that contain text/media, filtering by chat chat_filter & (~filters.COMMAND)
    ptb_app.add_handler(MessageHandler(chat_filter & (~filters.COMMAND), tg_message_handler))

    # Error Handler
    async def error_handler_func(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(f"Telegram Bot Error: {context.error}", exc_info=context.error)

    ptb_app.add_error_handler(error_handler_func)
