import httpx
from nonebot.log import logger

# Telegram generic utils

async def fetch_file(url: str, proxy: str = None) -> bytes:
    """Download file from URL"""
    try:
        async with httpx.AsyncClient(proxies=proxy, timeout=30) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        logger.error(f"Failed to download file {url}: {e}")
    return None
