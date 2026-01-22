import nonebot
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, MessageHandler, filters

from .client import ptb_app
from .config import plugin_config
from .vars import tg2qq, qq2tg
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
        # Check if we have a mapping
        # We have a TG Reply ID, we want the QQ ID it corresponds to.
        # Use tg2qq (Key: TG ID -> Value: QQ ID)
        if tg2qq[indx].get(reply_id):
            qq_id = tg2qq[indx].get(reply_id)
            qq_msg = f"[CQ:reply,id={qq_id}] " + qq_msg

    # Send to OneBot
    try:
        bot: Bot = nonebot.get_bot()
        result = await bot.send_group_msg(group_id=group_id, message=qq_msg)
        
        # Record mapping
        if result and 'message_id' in result:
            # TG message ID -> QQ message ID
            tg2qq[indx][msg.message_id] = result['message_id']
            # QQ message ID -> TG message ID (for reverse usage)
            qq2tg[indx][result['message_id']] = msg.message_id
             
    except Exception as e:
        logger.error(f"Failed to bridge TG -> QQ: {e}")

# Register handler
if ptb_app:
    # Filter for monitored chats only
    chat_filter = filters.Chat(chat_id=plugin_config.telegram_forward_chat)
    # Using generic ALL types that contain text/media, filtering by chat chat_filter & (~filters.COMMAND)
    ptb_app.add_handler(MessageHandler(chat_filter & (~filters.COMMAND), tg_message_handler))
