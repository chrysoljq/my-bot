from typing import List, Dict
from .config import plugin_config

# State variables
qq2dc: List[Dict[int, int]] = [{} for _ in plugin_config.discord_forward_group]
dc2qq: List[Dict[int, int]] = [{} for _ in plugin_config.discord_forward_group]
