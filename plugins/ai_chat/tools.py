
from typing import List, Dict, Any, Optional
import httpx
from nonebot import logger
from .config import config_manager
from .models import get_chat_history
from .openai_client import openai_client

# Define Tool Schemas
def get_tools_schema() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "view_image",
                "description": "仅在寻求技术支持/帮助时使用，其他情况请勿使用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt to describe the image."
                        },
                        "url": {
                            "type": "string",
                            "description": "The URL of the image to view."
                        }
                    },
                    "required": ["prompt", "url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "summarize_group",
                "description": "Summarize recent group chat history. Only available for bot owner.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt to summarize the group."
                        },
                        "user_id": {
                           "type": "integer",
                           "description": "The user ID invoking the command (for permission check)."
                        },
                         "hours": {
                            "type": "integer",
                            "description": "Hours of history to summarize (default 24).",
                            "default": 24
                        }
                    },
                    "required": ["prompt", "user_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ban_user",
                "description": "Ban a user from the group. Duration must be between 600s (10m) and 3600s (1h).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The user ID to ban."
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration in seconds (600-3600)."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the ban."
                        }
                    },
                    "required": ["group_id", "user_id", "duration"]
                }
            }
        }
    ]

# Tool Implementations
import base64
import ssl

ssl_context = ssl.create_default_context()
ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")

async def tool_view_image(prompt: str, url: str) -> str:
    """
    Calls OpenAI Vision to describe the image.
    Downloads image locally (with robust SSL) and sends Base64 to API.
    """
    logger.info(f"Tool view_image called for {url}")
    try:
        # Download image with specific SSL context
        async with httpx.AsyncClient(verify=ssl_context, timeout=30.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"Error downloading image: {resp.status_code}"
            
            image_bytes = resp.content
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            data_url = f"data:image/jpeg;base64,{base64_image}"

        # Construct a dedicated prompt for vision
        messages = [
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"{prompt}"},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ]
        
        description = ""
        async for chunk in openai_client.get_response(messages, tools=None): 
             description += chunk
        
        return f"[Image Description]: {description}"
    except Exception as e:
        logger.error(f"Failed to view image: {e}")
        return f"Error viewing image: {e}"

from nonebot.adapters.onebot.v11 import Bot

async def tool_ban_user(bot: Bot, group_id: int, user_id: int, duration: int, reason: str = "") -> str:
    """
    Ban a user.
    """
    logger.info(f"Tool ban_user called for {user_id} in {group_id} for {duration}s. Reason: {reason}")
    
    if duration < 600 or duration > 3600:
        return "Error: Duration must be between 600 and 3600 seconds."
        
    try:
        await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=duration)
        return f"Successfully banned user {user_id} for {duration}s."
    except Exception as e:
        logger.error(f"Failed to ban user: {e}")
        return f"Failed to ban user: {e}"

async def tool_summarize_group(prompt: str, group_id: int, user_id: int, hours: int = 24) -> str:
    """
    Summarizes group history.
    """
    logger.info(f"Tool summarize_group called for group {group_id} by {user_id}")
    
    # Permission Check
    if user_id != config_manager.bot_owner_id:
        return "Permission Denied: Only bot owner can request summary."
    
    try:
        history = await get_chat_history(group_id, limit=200)
        if not history:
            return "No history found."
        
        # Format for summary
        text_lines = []
        for msg in history:
            # Simple format: [Role] content
            role = "Bot" if msg['role'] == 'assistant' else f"User({msg['user_id']})"
            text_lines.append(f"{role}: {msg['content']}")
            
        full_text = "\n".join(text_lines)
        
        # Call OpenAI to summarize
        final_prompt = f"{prompt}\n\n{full_text}"
        
        messages = [{"role": "user", "content": final_prompt}]
        summary = ""
        async for chunk in openai_client.get_response(messages, tools=None):
            summary += chunk
            
        return f"[历史总结]: {summary}"

    except Exception as e:
        logger.error(f"Failed to summarize: {e}")
        return f"Error gathering summary: {e}"
