from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters import Message
from .db import db

clear_db_cmd = on_command("clear_db", aliases={"清除数据库"}, permission=SUPERUSER, priority=1, block=True)

@clear_db_cmd.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    arg_str = args.extract_plain_text().strip()
    
    # 获取所有非系统表
    # sqlite_sequence is internal, usually we don't want to drop it unless we want to reset autoincrement
    # but strictly speaking, dropping user tables is usually enough. 
    # Let's see what tables exist.
    try:
        rows = await db.fetchall("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        all_tables = [row['name'] for row in rows]
    except Exception as e:
        await clear_db_cmd.finish(f"Error fetching tables: {e}")
        return

    if not arg_str or arg_str == "list":
        if not all_tables:
            await clear_db_cmd.finish("Current database is empty (no user tables).")
        
        table_list = "\n".join([f"- {t}" for t in all_tables])
        await clear_db_cmd.finish(f"Current tables:\n{table_list}\n\nUsage:\n/clear_db all (Clear ALL)\n/clear_db <table_name> (Clear specific)")

    elif arg_str == "all":
        if not all_tables:
            await clear_db_cmd.finish("Database is already empty.")
            
        count = 0
        try:
            for table in all_tables:
                await db.execute(f"DROP TABLE IF EXISTS {table}")
                count += 1
            await clear_db_cmd.finish(f"Database cleared. Dropped {count} tables.")
        except Exception as e:
            await clear_db_cmd.finish(f"Error clearing database: {e}")

    else:
        # Clear specific table
        target_table = arg_str
        if target_table not in all_tables:
            await clear_db_cmd.finish(f"Table '{target_table}' not found.")
            
        try:
            await db.execute(f"DROP TABLE IF EXISTS {target_table}")
            await clear_db_cmd.finish(f"Table '{target_table}' dropped.")
        except Exception as e:
            await clear_db_cmd.finish(f"Error dropping table '{target_table}': {e}")
