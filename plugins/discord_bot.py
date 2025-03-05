import nonebot
import discord
from nonebot.log import logger
from discord import Message
import httpx
import io
import ssl
import asyncio
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.plugin import on_message as on_qqmsg


DRIVER = nonebot.get_driver()
MY_GROUP_LIST = []
MY_CHANNEL_ID = 1345354004196233286
FORWARD_GROUP = 1
FORWARD_CHANNEL = 1345742210993487902
qq2dc = {}
dc2qq = {}

ssl_context = ssl.create_default_context()
ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")  # 降低 OpenSSL 安全级别

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def is_mygroup(event: GroupMessageEvent):
    return event.self_id != event.sender.user_id and event.group_id == FORWARD_GROUP


async def fetch_image_bytes(url: str):
    """从URL获取图片的二进制数据"""
    async with httpx.AsyncClient(verify=ssl_context) as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.content  # 返回图片的二进制数据
        return None


@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')

# Discord to QQ


@client.event
async def on_message(message: Message):
    global dc2qq
    if message.author == client.user:
        return
    if message.channel.id != MY_CHANNEL_ID and message.channel.id != FORWARD_CHANNEL:
        return

    bot = nonebot.get_bot()
    msg = f"Discord通知(来自{message.author})：\n{message.content}"

    # if message.reference: # 转发消息
    #     message = await message.channel.fetch_message(message.reference.message_id)

    if message.attachments:  # 附件
        for attachment in message.attachments:
            # logger.info(attachment.content_type)
            # if attachment.content_type.startswith("video/"):
            #     logger.info(attachment.url)
            #     msg = f"[CQ:video,file={attachment.url}]"
            #     return
            msg += f"[CQ:image,file={attachment.url}]"

    if message.channel.id == FORWARD_CHANNEL:
        if message.reference:
            msg_id = message.reference.message_id
            if qq2dc.get(msg_id):
                msg = f"[CQ:reply,id={qq2dc.get(msg_id)}] "+msg
        result = await bot.send_group_msg(group_id=FORWARD_GROUP, message=msg)
        dc2qq[result.get('data').get('message_id')] = message.id
        # print(qq2dc,result.get('data').get('message_id'))
        return

    for group in MY_GROUP_LIST:
        await bot.call_api('send_group_msg', group_id=group, message=msg)
        logger.info(
            f"Message From Discord {message.embeds}=={message.reference}")

# @client.event
# async def on_disconnect():
#     print("断开连接，正在尝试重连...")
#     await client.close()
#     await client.start("YOUR_BOT_TOKEN")


forward_bot = on_qqmsg(rule=is_mygroup)


@forward_bot.handle()
async def forward_handle(event: GroupMessageEvent):
    global qq2dc
    msgs = event.message
    forward_msg = f'<{event.sender.nickname}({event.sender.user_id})> '
    files = []
    for msg in msgs:
        if msg.type == 'text':
            forward_msg += msg.data['text']+'\n'
        if msg.type == 'image' or msg.type == 'video':
            image_data = await fetch_image_bytes(msg.data['file'])
            if image_data:
                file = discord.File(io.BytesIO(image_data),
                                    filename="image.png")
                files.append(file)

    result = await client.get_channel(FORWARD_CHANNEL).send(forward_msg, files=files)
    qq2dc[result.id] = event.message_id


@DRIVER.on_bot_connect
async def main():
    # asyncio.to_thread()
    await client.start('')


@DRIVER.on_bot_disconnect
async def stop():
    await client.close()
