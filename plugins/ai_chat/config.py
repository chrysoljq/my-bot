
import json
from pathlib import Path
from typing import List, Dict, Any
from nonebot import logger

CONFIG_PATH = Path("data/aichat/config.json")

class ConfigManager:
    def __init__(self):
        self.config: Dict[str, Any] = {
            "openai_api_key": "",
            "openai_api_base": "https://api.openai.com/v1",
            "openai_model": "gpt-3.5-turbo",
            "bot_owner_id": 0,
            "enabled_groups": []
        }
        self.load_config()

    def load_config(self):
        if not CONFIG_PATH.exists():
            self.save_config()
            return

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.config.update(data)
        except Exception as e:
            logger.error(f"Failed to load aichat config: {e}")

    def save_config(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save aichat config: {e}")

    @property
    def openai_api_key(self) -> str:
        return self.config.get("openai_api_key", "")

    @property
    def openai_api_base(self) -> str:
        return self.config.get("openai_api_base", "https://api.openai.com/v1")
    
    @property
    def openai_model(self) -> str:
        return self.config.get("openai_model", "gpt-3.5-turbo")

    @property
    def bot_owner_id(self) -> int:
        return self.config.get("bot_owner_id", 0)

    @property
    def enabled_groups(self) -> List[int]:
        return self.config.get("enabled_groups", [])

    def enable_group(self, group_id: int):
        if group_id not in self.enabled_groups:
            self.enabled_groups.append(group_id)
            self.save_config()

    def disable_group(self, group_id: int):
        if group_id in self.enabled_groups:
            self.enabled_groups.remove(group_id)
            self.save_config()

config_manager = ConfigManager()
