import websockets
import asyncio
import json
from collections import defaultdict
import time
import hmac
import base64
import hashlib
from ASSETS import ASSETS

# Authentication details
api_key = Removed
api_secret = Removed

# Use the OX codes from the config
tickers = [asset['ox_code'] for asset in ASSETS]
url = 'wss://api.ox.fun/v2/websocket'

latest_data = defaultdict(dict)

def get_auth_message():
    ts = str(int(time.time() * 1000))
    sig_payload = (ts+'GET/auth/self/verify').encode('utf-8')
    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), sig_payload, hashlib.sha256).digest()).decode('utf-8')

    return {
        "op": "login",
        "tag": 1,
        "data": {
            "apiKey": api_key,
            "timestamp": ts,
            "signature": signature
        }
    }

def chunk_tickers(tickers, chunk_size=50):
    for i in range(0, len(tickers), chunk_size):
        yield tickers[i:i + chunk_size]

async def process_message(ws):
    while True:
        response = await ws.recv()
        data = json.loads(response)
        
        if 'table' in data and data['table'] == 'depthL5':
            market_code = data['data']['marketCode']
            latest_data[market_code] = {
                'bid': data['data']['bids'][0][0],
                'ask': data['data']['asks'][0][0]
            }

async def fetch_ox_prices():
    while True:
        try:
            async with websockets.connect(url) as ws:
                auth_message = get_auth_message()
                await ws.send(json.dumps(auth_message))
                
                auth_response = await ws.recv()
                print(auth_response)
                
                for chunk in chunk_tickers(tickers):
                    orderbook_depth = {
                        "op": "subscribe",
                        "tag": 103,
                        "args": [f"depthL5:{ticker}" for ticker in chunk]
                    }
                    await ws.send(json.dumps(orderbook_depth))
                
                await process_message(ws)
        except Exception as e:
            print(f"OX connection error: {e}")
            await asyncio.sleep(1)  # Wait before reconnecting

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(fetch_ox_prices())
