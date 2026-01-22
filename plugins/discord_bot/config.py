from typing import List, Optional
from pydantic import BaseModel, Field
from nonebot import get_plugin_config

class Config(BaseModel):
    discord_token: str = Field(default="")
    discord_proxy: Optional[str] = Field(default=None)
    
    # 公告列表
    discord_my_group_list: List[int] = Field(default_factory=list)
    discord_my_channel_id: int = Field(default=0)
    
    # 转发对应列表
    discord_forward_group: List[int] = Field(default_factory=list)
    discord_forward_channel: List[int] = Field(default_factory=list)
    
    # 屏蔽/白名单列表
    discord_black_qq: List[int] = Field(default_factory=list)
    discord_black_dc: List[int] = Field(default_factory=list) # Changed to int to match usage (IDs)
    discord_white_dc: List[int] = Field(default_factory=list)
    
    discord_command_dc: List[str] = Field(default=['.analysis', '.help', '.status'])

# Try to use get_plugin_config, fallback if needed (though pydantic v2 usually implies newer nonebot)
try:
    plugin_config = get_plugin_config(Config)
except ImportError:
    # Fallback for older NoneBot versions
    from nonebot import get_driver
    driver = get_driver()
    plugin_config = Config.parse_obj(driver.config.dict())
except Exception as e:
    # If get_plugin_config fails for some reason (e.g. validatin), let it raise properly or handle?
    # But usually it's the right way.
    # The user error was 'input should be a valid dictionary or instance of Config'.
    # get_plugin_config handles extraction.
    raise e
