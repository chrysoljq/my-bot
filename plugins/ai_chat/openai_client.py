
import json
import httpx
from typing import List, Dict, AsyncGenerator, Any, Optional
from nonebot import logger
from .config import config_manager

class OpenAIClient:
    def __init__(self):
        pass

    async def get_response(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        
        api_key = config_manager.openai_api_key
        base_url = config_manager.openai_api_base
        model = config_manager.openai_model

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        url = f"{base_url.rstrip('/')}/chat/completions"

        # State to track tool calls across chunks
        current_tool_calls: Dict[int, Dict[str, Any]] = {}

        try:
            async with httpx.AsyncClient(timeout=240) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_msg = await response.aread()
                        logger.error(f"OpenAI API Error {response.status_code}: {error_msg.decode('utf-8')}")
                        yield f"Error: API returned {response.status_code}"
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0]["delta"]
                                
                                # Handle Content
                                if "content" in delta and delta["content"]:
                                    yield delta["content"]
                                
                                # Handle Tool Calls
                                if "tool_calls" in delta and delta["tool_calls"]:
                                    for tc in delta["tool_calls"]:
                                        index = tc["index"]
                                        if index not in current_tool_calls:
                                            current_tool_calls[index] = {
                                                "id": "", "type": "function", 
                                                "function": {"name": "", "arguments": ""}
                                            }
                                        
                                        if "id" in tc:
                                            current_tool_calls[index]["id"] += tc["id"]
                                        if "function" in tc:
                                            if "name" in tc["function"]:
                                                current_tool_calls[index]["function"]["name"] += tc["function"]["name"]
                                            if "arguments" in tc["function"]:
                                                current_tool_calls[index]["function"]["arguments"] += tc["function"]["arguments"]

                            except json.JSONDecodeError:
                                continue
                            except Exception as e:
                                logger.warning(f"Error parsing chunks: {e}")
            
            # If we collected tool calls, we need to yield them somehow.
            # But this generator yields strings (content).
            # To handle tool calls in a streaming generator is tricky if the caller expects strings.
            # Convention: Yield a special marker or JSON structure?
            # Or simpler: The caller should handle the buffer.
            # PROBLEM: "yield" returns to the caller loop.
            # If we have tool calls, we should probably output them as a special JSON string
            # that the caller can parse.
            
            if current_tool_calls:
                # Reconstruct full tool calls
                tool_calls_list = [v for k, v in sorted(current_tool_calls.items())]
                # Yield as a special protocol string or just the raw function call for debug?
                # The caller (__init__.py) needs to execute this.
                # Let's serialize it.
                yield f"|||TOOL_CALLS|||{json.dumps(tool_calls_list)}"

        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            yield f"Request failed: {str(e)}"

openai_client = OpenAIClient()
