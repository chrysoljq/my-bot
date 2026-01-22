import json
from pathlib import Path
from typing import Set
from .config import plugin_config

DATA_PATH = Path("data/telegram_bot/whitelist.json")

class WhitelistManager:
    def __init__(self):
        self.whitelist: Set[int] = set()
        self.load()

    def load(self):
        if DATA_PATH.exists():
            try:
                with open(DATA_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.whitelist = set(data.get("whitelist", []))
            except Exception:
                self.whitelist = set()
        else:
            self.whitelist = set()

    def save(self):
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump({"whitelist": list(self.whitelist)}, f)

    def add(self, user_id: int):
        self.whitelist.add(user_id)
        self.save()

    def remove(self, user_id: int):
        if user_id in self.whitelist:
            self.whitelist.remove(user_id)
            self.save()

    def is_allowed(self, user_id: int) -> bool:
        # Check Bot Owner (Global Admin)
        if plugin_config.bot_owner and user_id == plugin_config.bot_owner:
            return True

        # If whitelist is empty, force return False (Whitelist Mode Enforced as per user change)
        if not self.whitelist:
            return False
            
        return user_id in self.whitelist

    def get_all(self) -> list:
        return list(self.whitelist)

whitelist_manager = WhitelistManager()
