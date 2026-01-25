
from nonebot import on_command, on_message, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
import random
import time
import json

from .config import config_manager
from .models import init_db, save_message, get_chat_history
from .utils import render_prompt, format_history_message, append_group_memory, load_all_group_memories, save_all_group_memories
from .openai_client import openai_client
from .tools import get_tools_schema, tool_view_image, tool_summarize_group, tool_ban_user

__plugin_meta__ = PluginMetadata(
    name="AI Chat",
    description="Roleplay AI Chat for QQ Groups (Tools & Vision)",
    usage="@bot or start with 'ai'"
)

driver = get_driver()

@driver.on_startup
async def _():
    await init_db()
    load_all_group_memories()

@driver.on_shutdown
async def _():
    save_all_group_memories()

# 开关ai群聊
cmd_aichat = on_command("aichat", priority=1, block=True)
cmd_save = on_command("save_memory", priority=1, block=True)

@cmd_save.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not (await SUPERUSER(bot, event)):
        return
    save_all_group_memories()
    await cmd_save.finish("Memory saved manually.")

@cmd_aichat.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if not (await SUPERUSER(bot, event)):
        await cmd_aichat.finish("Permission denied.")

    arg_str = args.extract_plain_text().strip()
    if arg_str == "on":
        group_id = event.group_id
        if group_id not in config_manager.enabled_groups:
            config_manager.enable_group(event.group_id)
        await cmd_aichat.finish(f"AI Chat enabled for group {event.group_id}")
    elif arg_str == "off":
        group_id = event.group_id
        if group_id in config_manager.enabled_groups:
            config_manager.disable_group(event.group_id)
        await cmd_aichat.finish(f"AI Chat disabled for group {event.group_id}")
    else:
        await cmd_aichat.finish("Usage: /aichat on/off")

# Message Handler
async def ai_checker(event: GroupMessageEvent) -> bool:
    return (
        event.group_id in config_manager.enabled_groups and
        (
            event.is_tome() or 
            event.get_plaintext().strip().lower().startswith("ai ") or 
            random.random() < 0.01 or
            (random.random() < 0.2 and '怎么' in event.get_plaintext())
        )
    )


# Message Recorder (Logs all messages in enabled groups)
async def recorder_checker(event: GroupMessageEvent) -> bool:
    return event.group_id in config_manager.enabled_groups

message_recorder = on_message(rule=recorder_checker, priority=1, block=False)
@message_recorder.handle()
async def _(event: GroupMessageEvent):
    if event.user_id == 1878818381: # 跳过本人信息
        return
    content = str(event.get_message())
    if content.lower().startswith("ai "):
        content = content[3:].strip()

    nick_name = event.sender.card if event.sender.card else event.sender.nickname
    await save_message(event.group_id, nick_name, event.user_id, "user", content, int(time.time()))

# AI Responder (Triggered by Rule)
ai_message = on_message(rule=ai_checker)

@ai_message.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    # Build Context
    # Build Context
    history = await get_chat_history(event.group_id, limit=50)
    timestamp = int(time.time()) # 把收到请求的时间戳作为回复时间
    
    # group_name = " "
    
    system_prompt = render_prompt(event.group_id) # .replace("{{GROUP_NAME}}", group_name)

    messages = [{"role": "system", "content": system_prompt}]

    for msg in history:
        role = "assistant" if msg['role'] == "assistant" else "user"
        content = msg['content'] if role == "assistant" else format_history_message(msg)
        
        if messages and messages[-1]['role'] == role:
            messages[-1]['content'] += "\n" + content
        else:
            messages.append({"role": role, "content": content})
            
    # Logging for verification
    # logger.debug(f"AI Chat Context: {len(messages)} messages loaded.")

    # Helper to process response stream
    async def process_stream():
        response_buffer = ""
        tool_calls_json = None
        
        async for chunk in openai_client.get_response(messages, tools=get_tools_schema()):
            if chunk.startswith("|||TOOL_CALLS|||"):
                tool_calls_json = chunk.split("|||TOOL_CALLS|||")[1]
            else:
                response_buffer += chunk

        return response_buffer, tool_calls_json

    # Initial Call
    try:
        final_content, tool_calls_json = await process_stream()
        
        # Handle Tool Calls
        if tool_calls_json:
            tool_calls = json.loads(tool_calls_json)
            messages.append({"role": "assistant", "content": final_content, "tool_calls": tool_calls})
            
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                args_str = tc["function"]["arguments"]
                args = json.loads(args_str)
                call_id = tc["id"]
                
                tool_result = "Unknown Tool"
                if func_name == "view_image":
                    tool_result = await tool_view_image(
                        args.get("prompt"),
                        args.get("url"))
                elif func_name == "summarize_group":
                    tool_result = await tool_summarize_group(
                        args.get("prompt"),
                        event.group_id, 
                        event.user_id, # Pass actual user_id for permission check
                        args.get("hours", 24)
                    )
                elif func_name == "ban_user":
                    tool_result = await tool_ban_user(
                        bot,
                        event.group_id,
                        args.get("user_id"),
                        args.get("duration"),
                        args.get("reason", "")
                    )
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": tool_result
                })
            
            # Second Call (Post-Tool)
            final_content, _ = await process_stream() # Recursive? Ideally loop, but 1 depth is usually enough for this bot.

        # Process Final Output (Ban logic etc)
        final_content = final_content.strip()
        
        
        # Output final content
        if final_content.startswith("|||"):
            final_content = final_content[3:].strip()
            
        parts = final_content.split("|||")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check for MEM tag
            if part.startswith("[MEM:"):
                # Extract content
                mem_content = part[5:]
                if mem_content.endswith("]"):
                    mem_content = mem_content[:-1]
                
                # Save to memory
                append_group_memory(event.group_id, mem_content.strip())
                # Don't send this part!
                continue
            
            await bot.send_group_msg(group_id=event.group_id, message=part)
            await save_message(event.group_id, "人工质能", event.self_id, "assistant", part, timestamp)

    except Exception as e:
        await ai_message.finish(f"Error: {e}")
