import asyncio
import io
import discord
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.log import logger
from .matcher import forward_bot
from .config import plugin_config
from .utils import fetch_image_bytes, is_gif
from .client import client
from plugins.datastore import db

@forward_bot.handle()
async def forward_handle(event: GroupMessageEvent):
    # global qq2dc
    try:
        indx = plugin_config.discord_forward_group.index(event.group_id)
    except ValueError:
        return # Should not happen due to matcher rule

    msgs = event.original_message
    forward_msg = f'<{event.sender.card if event.sender.card else event.sender.nickname}({event.sender.user_id})> '
    files = []
    reply_message_id = None
    
    for msg in msgs:
        if msg.type == 'text':
            forward_msg += msg.data['text']+'\n'
        elif msg.type == 'at':
            forward_msg += f"{msg.data.get('name', '@')}({msg.data.get('qq')}) "
        elif msg.type in ('image', 'video'):
            image_data = await fetch_image_bytes(msg.data['file'])
            if image_data:
                file = discord.File(io.BytesIO(image_data),
                                    filename="image.gif" if is_gif(image_data) else "image.png")
                files.append(file)
        elif msg.type == 'reply':
            qq_reply_id = int(msg.data.get('id'))
            
            # Check DB for Discord Msg ID
            row = await db.fetchone(
                "SELECT discord_id FROM discord_msg_map WHERE qq_id = ? AND channel_id = ?",
                (qq_reply_id, plugin_config.discord_forward_channel[indx])
            )
            if row:
                reply_message_id = row['discord_id']

    # 掉线重启
    try:
        channel_id = plugin_config.discord_forward_channel[indx]
        channel = client.get_channel(channel_id)
        if not channel:
            logger.error(f"Channel {channel_id} not found/cached.")
            # possibly fetch it?
            try:
                channel = await client.fetch_channel(channel_id)
            except:
                logger.error(f"Result: Could not fetch channel {channel_id}")
                return

        if reply_message_id:
            try:
                ref = await channel.fetch_message(reply_message_id)
                result = await ref.reply(forward_msg, files=files) 
                # Note: files arg was missing in original replay branch? 
                # Original: result = await ref.reply(forward_msg) 
                # But it constructed files. Let's add files=files to be better.
            except discord.NotFound:
                # Referenced message gone, send as normal
                result = await channel.send(forward_msg, files=files)
        else:
            result = await channel.send(forward_msg, files=files)
            
        if result:
             # Save to DB: Discord ID -> QQ ID (Result) ??? 
             # Wait, logic is: user sends QQ msg -> Bot forwards to Discord.
             # We want to know that this Discord Msg corresponds to this QQ Msg.
             # So if someone replies to this Discord Msg, we know which QQ Msg to reply to?
             # Yes.
             # discord_msg_map keys: discord_id, qq_id, channel_id.
             
            await db.execute(
                "INSERT INTO discord_msg_map (discord_id, qq_id, channel_id) VALUES (?, ?, ?)",
                (result.id, event.message_id, channel_id)
            )
        
    except RuntimeError:
        logger.warning('discord client has been closed, restarting..')
        await client.close()
        await asyncio.sleep(5)
        await client.start(plugin_config.discord_token, reconnect=True)
    except Exception as e:
        logger.error(f"Error forwarding to Discord: {e}")
