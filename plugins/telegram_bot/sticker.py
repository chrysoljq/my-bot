from telegram import Sticker
from nonebot.log import logger

async def get_sticker_cq(sticker: Sticker) -> str:
    """
    Parse a Telegram sticker and return a CQ code for OneBot.
    Best effort:
    - If static (webp): Send as image.
    - If video (webm) or animated (tgs): Try to send thumbnail if available, or just text.
    """
    try:
        # Telegram stickers:
        # - is_animated=True -> .tgs (Lottie)
        # - is_video=True -> .webm
        # - otherwise -> .webp (Static)

        file = await sticker.get_file()
        url = file.file_path
        
        # If it's a static sticker, we can usually send it as an image.
        if not sticker.is_animated and not sticker.is_video:
            return f"[CQ:image,file={url}]"
        
        # If it's video/animated, we might want to send the thumbnail if it exists
        if sticker.thumbnail:
            # Thumbnail is a PhotoSize object
            thumb_file = await sticker.thumbnail.get_file()
            thumb_url = thumb_file.file_path
            # Provide a fallback text indicating it's animated
            emoji = sticker.emoji if sticker.emoji else ""
            return f"[CQ:image,file={thumb_url}]"

        # Fallback for no thumbnail
        emoji = sticker.emoji if sticker.emoji else "sticker"
        return f"[TG Sticker {emoji}]"

    except Exception as e:
        logger.error(f"Error parsing sticker: {e}")
        return "[Sticker Error]"
