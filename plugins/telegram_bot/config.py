from typing import List, Optional
from pydantic import BaseModel, Field
from nonebot import get_plugin_config

class Config(BaseModel):
    # Field alias handling usually needs ConfigDict in V2, or allow_population_by_field_name in V1.
    # NoneBot get_plugin_config handles environment variable mapping but uses specific rules.
    # Usually `BOT_OWNER` in env maps to `bot_owner` in model if no prefix is set,
    # OR if prefix is set (e.g. NONEBOT_), then NONEBOT_BOT_OWNER.
    
    # If the user put BOT_OWNER in .env, checking if it is getting picked up.
    # NoneBot config extraction is case-insensitive usually.
    
    bot_owner: int = Field(default=0)
    
    telegram_token: str = Field(default="")
    telegram_proxy: Optional[str] = Field(default=None)
    
    # 转发对应列表: index i of group corresponds to index i of chat
    telegram_forward_group: List[int] = Field(default_factory=list)
    telegram_forward_chat: List[int] = Field(default_factory=list) 
    telegram_forward_topic: List[int] = Field(default_factory=list) # Optional: Topic/Thread IDs

try:
    plugin_config = get_plugin_config(Config)
except ImportError:
    from nonebot import get_driver
    driver = get_driver()
    plugin_config = Config.parse_obj(driver.config.dict())
except Exception as e:
    raise e
