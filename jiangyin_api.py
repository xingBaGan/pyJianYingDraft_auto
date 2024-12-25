import requests
import aiohttp

async def export_video(filename):
    # 方案1: 使用 aiohttp 库 (推荐)
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/export', json={'filename': filename}) as response:
            print('response', response)
            return response
        
async def create_draft(filename):
    # 方案1: 使用 aiohttp 库 (推荐)
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/create_draft', json={'filename': filename}) as response:
            return response
        
async def publish_to_web(data):
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/publish_to_web', json=data) as response:
            return response