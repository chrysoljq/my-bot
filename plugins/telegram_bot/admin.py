from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.permission import SUPERUSER
from .client import ptb_app

tg_status = on_command("tg_status")

@tg_status.handle()
async def handle_status(event: GroupMessageEvent):
    msg = "Telegram Bot Status:\n"
    
    if not ptb_app:
        msg += "❌ App not initialized (Config missing?)"
        await tg_status.finish(msg)
        return

    # Check App Loop
    if ptb_app.running:
        msg += "✅ Application Running\n"
    else:
        msg += "❌ Application STOPPED\n"

    # Check Polling
    if ptb_app.updater and ptb_app.updater.running:
        msg += "✅ Updater (Polling) Running\n"
    else:
        msg += "❌ Updater STOPPED (Not Polling)\n"
        
    # Check Initialization
    if ptb_app._initialized:
         msg += "✅ Initialized"
    else:
         msg += "⚠️ Not Initialized"

    await tg_status.finish(msg)
