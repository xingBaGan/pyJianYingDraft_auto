import requests
import aiohttp

async def export_video(filename):
    # 方案1: 使用 aiohttp 库 (推荐)
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/export', json={'filename': filename}) as response:
            print('response', response)
            return response