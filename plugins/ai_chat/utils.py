
from typing import List, Dict, Any
import datetime


from pathlib import Path
from nonebot import logger

PERSONA_PATH = Path("data/aichat/persona_v2.md")
MEMORY_DIR = Path("data/aichat/memory")
MEMORY_CACHE: Dict[int, str] = {}

def load_persona() -> str:
    if not PERSONA_PATH.exists():
        return "Error: Persona file not found."
    try:
        return PERSONA_PATH.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to load persona: {e}")
        return "Error loading persona."

def load_all_group_memories():
    """Load all memory files into cache at startup"""
    if not MEMORY_DIR.exists():
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        return

    try:
        count = 0
        for mem_file in MEMORY_DIR.glob("*.txt"):
            try:
                # Filename is group_id.txt
                group_id_str = mem_file.stem
                if group_id_str.isdigit():
                    group_id = int(group_id_str)
                    MEMORY_CACHE[group_id] = mem_file.read_text(encoding="utf-8")
                    count += 1
            except Exception as e:
                logger.error(f"Failed to load memory file {mem_file}: {e}")
        logger.info(f"Loaded {count} group memories.")
    except Exception as e:
        logger.error(f"Failed to load all memories: {e}")

def save_all_group_memories():
    """Save all cached memories to disk"""
    if not MEMORY_DIR.exists():
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for group_id, content in MEMORY_CACHE.items():
        try:
            mem_file = MEMORY_DIR / f"{group_id}.txt"
            # We are writing the FULL content, because cache holds the full history
            mem_file.write_text(content, encoding="utf-8")
            count += 1
        except Exception as e:
            logger.error(f"Failed to save memory for group {group_id}: {e}")
    logger.info(f"Saved {count} group memories.")

def load_group_memory(group_id: int) -> str:
    # On-demand load only if cache is empty? 
    # User requested start-load, but if a new group comes in, it won't have a file yet.
    # Return from cache or default.
    return MEMORY_CACHE.get(group_id, "暂无长期记忆。")

def append_group_memory(group_id: int, content: str):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_entry = f"[{timestamp}] {content}\n"
    
    # Update Cache ONLY
    if group_id in MEMORY_CACHE:
        MEMORY_CACHE[group_id] += new_entry
    else:
        MEMORY_CACHE[group_id] = new_entry

def render_prompt(group_id: int) -> str:
    template = load_persona()
    memory = load_group_memory(group_id)
    
    prompt = template.replace("{{GROUP_ID}}", str(group_id))\
        .replace("{{MEMORY}}", memory)
        
    return prompt

def format_history_message(msg: Dict[str, Any]) -> str:
    timestamp = datetime.datetime.fromtimestamp(msg['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
    user_str = f"{msg['nick_name']}({msg['user_id']})"
    if msg['role'] == 'assistant':
        user_str = "风之遗迹(2190481526)"
         
    return f"[{timestamp}][{user_str}]：{msg['content']}"
