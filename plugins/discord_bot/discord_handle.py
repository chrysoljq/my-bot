import nonebot
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger
from discord import Message
from .client import client
from .config import plugin_config
from .vars import qq2dc, dc2qq

@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')

@client.event
async def on_message(message: Message):
    # global dc2qq # Imported from vars, it is a mutable list, so modification works.
    
    if message.author == client.user:
        return
    if message.channel.id != plugin_config.discord_my_channel_id and message.channel.id not in plugin_config.discord_forward_channel:
        return

    try:
        bot: Bot = nonebot.get_bot()
    except ValueError:
        logger.warning("No OneBot instance connected.")
        return

    if message.content in plugin_config.discord_command_dc:
        msg = message.content
    else:
        msg = f"<discord>({message.author.display_name})：{message.content}"
    
    if message.attachments:  # 附件
        for attachment in message.attachments:
            logger.info(f"Attachment: {attachment.content_type}, {attachment.url}")
            if not attachment.content_type.startswith("image/"):
                logger.info(attachment.url)
                msg = f"附件：{attachment.url}"
            msg += f"[CQ:image,file={attachment.url}]"

    if message.channel.id in plugin_config.discord_forward_channel:
        indx = plugin_config.discord_forward_channel.index(message.channel.id)
        
        # Hardcoded logic in original code:
        # if (indx == 1 and message.author.id not in FORWORD_WHITE_DC) and message.content not in FORWORD_COMMAND_DC:
        # We need to adapt this. Is index 1 specific? 
        # Original: if (indx == 1 and message.author.id not in FORWORD_WHITE_DC) ...
        # I will preserve this logic but use config.
        # Assuming indx 1 refers to a specific channel that needs whitelist.
        # Since we don't know which one, we might keep it or generalize. 
        # The user asked to move config to .env. If I can't generalize "indx == 1", I'll keep it as is for now.
        
        if (indx == 1 and message.author.id not in plugin_config.discord_white_dc) and message.content not in plugin_config.discord_command_dc:
            return

        if message.reference:
            msg_id = message.reference.message_id
            if qq2dc[indx].get(msg_id):
                msg = f"[CQ:reply,id={qq2dc[indx].get(msg_id)}] "+msg
        
        try:
            result = await bot.send_group_msg(group_id=plugin_config.discord_forward_group[indx], message=msg)
            dc2qq[indx][result.get('message_id')] = message.id
        except Exception as e:
            logger.error(f"Failed to send group msg: {e}")
        return

    for group in plugin_config.discord_my_group_list:
        try:
            await bot.call_api('send_group_msg', group_id=group, message=msg)
            logger.info(f"Message From Discord forwarded to group {group}")
        except Exception as e:
            logger.error(f"Failed to broadcast to group {group}: {e}")
