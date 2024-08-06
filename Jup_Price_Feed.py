import asyncio
import aiohttp
import json
from collections import defaultdict
from ASSETS import ASSETS

# Use the Jupiter codes from the config
tokens = [asset['jupiter_code'] for asset in ASSETS]

url = 'https://price.jup.ag/v4/price'

latest_data = defaultdict(dict)

def chunk_tokens(tokens, chunk_size=100):
    for i in range(0, len(tokens), chunk_size):
        yield tokens[i:i + chunk_size]

async def fetch_prices_chunk(session, token_chunk):
    params = {'ids': ','.join(token_chunk)}
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            for token in token_chunk:
                if 'data' in data and token in data['data']:
                    price = data['data'][token]['price']
                    latest_data[token] = {'price': price}
        else:
            print(f"Failed to fetch prices for chunk. Status code: {response.status}")

async def fetch_jupiter_prices():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for chunk in chunk_tokens(tokens):
                    task = asyncio.create_task(fetch_prices_chunk(session, chunk))
                    tasks.append(task)
                await asyncio.gather(*tasks)
            await asyncio.sleep(1)  # Fetch every second
        except Exception as e:
            print(f"Jupiter API error: {e}")
            await asyncio.sleep(1)  # Wait before retrying

if __name__ == "__main__":
    asyncio.run(fetch_jupiter_prices())