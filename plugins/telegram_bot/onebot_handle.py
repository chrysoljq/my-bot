import asyncio
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.log import logger
from telegram import InputMediaPhoto
from telegram.constants import ParseMode

from .matcher import forward_bot
from .config import plugin_config
from .client import ptb_app
from .utils import fetch_file
from plugins.datastore import db

@forward_bot.handle()
async def onebot_to_tg(event: GroupMessageEvent):
    if not ptb_app:
        return

    try:
        indx = plugin_config.telegram_forward_group.index(event.group_id)
    except ValueError:
        return

    chat_id = plugin_config.telegram_forward_chat[indx]
    
    topic_id = None
    if indx < len(plugin_config.telegram_forward_topic):
        topic_id = plugin_config.telegram_forward_topic[indx]
        if topic_id == 0:
            topic_id = None # convert 0 back to None for PTB
            
    sender_name = event.sender.card or event.sender.nickname
    user_id = event.sender.user_id
    
    prefix = f"<b>&lt;{sender_name}({user_id})&gt;</b>\n"
    
    msgs = event.original_message
    text_buffer = ""
    files_to_send = [] # (type, data/url)
    
    reply_tg_id = None

    for msg in msgs:
        if msg.type == 'text':
            text_buffer += msg.data['text']
        elif msg.type == 'at':
            text_buffer += f"{msg.data.get('name', msg.data.get('qq'))} "
        elif msg.type == 'image':
            url = msg.data.get('url')
            if url:
                files_to_send.append(('photo', url))
        elif msg.type == 'reply':
            qq_id = int(msg.data.get('id'))
            # Check DB
            row = await db.fetchone(
                "SELECT tg_id FROM tg_msg_map WHERE qq_id = ? AND group_index = ?",
                (qq_id, indx)
            )
            if row:
                reply_tg_id = row['tg_id']

    full_text = prefix + text_buffer
    
    try:
        sent_msg = None
        
        # If simple text
        if not files_to_send:
            sent_msg = await ptb_app.bot.send_message(
                chat_id=chat_id,
                message_thread_id=topic_id, # Target topic
                text=full_text,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=reply_tg_id
            )
        else:
            # If has images
            # PTB send_photo or send_media_group
            # If 1 photo
            if len(files_to_send) == 1:
                # Caption limit is 1024 chars
                sent_msg = await ptb_app.bot.send_photo(
                    chat_id=chat_id,
                    message_thread_id=topic_id, # Target topic
                    photo=files_to_send[0][1],
                    caption=full_text[:1024],
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=reply_tg_id
                )
            else:
                # Group
                media = []
                for i, (ftype, furl) in enumerate(files_to_send):
                    # Only first item gets caption usually in group, or separate?
                    # Telegram media group caption is on the first item
                    cap = full_text[:1024] if i == 0 else None
                    if ftype == 'photo':
                        media.append(InputMediaPhoto(media=furl, caption=cap, parse_mode=ParseMode.HTML))
                
                msgs_list = await ptb_app.bot.send_media_group(
                    chat_id=chat_id,
                    message_thread_id=topic_id, # Target topic
                    media=media,
                    reply_to_message_id=reply_tg_id
                )
                if msgs_list:
                    sent_msg = msgs_list[0] # Just map to first one?

        if sent_msg:
            # Save mapping to DB
            # QQ message ID (source) -> TG message ID (target)
            await db.execute(
                "INSERT INTO tg_msg_map (tg_id, qq_id, group_index) VALUES (?, ?, ?)",
                (sent_msg.message_id, event.message_id, indx)
            )

    except Exception as e:
        logger.error(f"Failed to bridge QQ -> TG: {e}")
