from typing import List, Dict
from .config import plugin_config

# Maps: index -> {msg_id_map}
# Structure: List of Dict[source_msg_id, target_msg_id]
qq2tg: List[Dict[int, int]] = [{} for _ in plugin_config.telegram_forward_group]
tg2qq: List[Dict[int, int]] = [{} for _ in plugin_config.telegram_forward_group]
