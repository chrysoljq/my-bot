import httpx
import ssl
from nonebot.log import logger

ssl_context = ssl.create_default_context()
ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")  # 降低 OpenSSL 安全级别

def is_gif(data: bytes) -> bool:
    return data.startswith(b'GIF')

async def fetch_image_bytes(url: str):
    """从URL获取图片的二进制数据"""
    try:
        async with httpx.AsyncClient(verify=ssl_context, timeout=10) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content  # 返回图片的二进制数据
            return None
    except:
        logger.error(f"Failed to fetch image from {url}")
