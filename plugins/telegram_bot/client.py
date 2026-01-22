from telegram.ext import Application
from .config import plugin_config

# Initialize PTB Application
# Note: ApplicationBuilder().build() creates the app.
# We will start it manually in __init__.py

if plugin_config.telegram_token:
    ptb_app = Application.builder().token(plugin_config.telegram_token)
    if plugin_config.telegram_proxy:
        ptb_app = ptb_app.proxy_url(plugin_config.telegram_proxy).get_updates_proxy_url(plugin_config.telegram_proxy)
    
    ptb_app = ptb_app.build()
else:
    ptb_app = None
