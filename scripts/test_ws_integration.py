import asyncio
import json
import redis.asyncio as aioredis
import websockets
import time

REDIS_URL = "redis://localhost:6379/0"
WS_URL = "ws://localhost:8080/ws"

async def test_ws_integration():
    print("--- Starting WebSocket Integration Test ---")
    
    # Connect to Redis
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    
    # Connect to WebSocket
    async with websockets.connect(WS_URL) as websocket:
        print(f"Connected to WebSocket at {WS_URL}")
        
        # Define test messages
        test_messages = [
            ("price:BTC", {"ticker": "BTC", "close": 50000.0, "timestamp": "2026-03-16T10:00:00Z"}),
            ("sentiment:BTC", {"symbol": "BTC", "sentiment_score": 0.8, "sentiment_label": "positive"}),
            ("forecast:BTC", {"ticker": "BTC", "model_type": "lstm", "predictions": [51000, 52000]}),
            ("alerts:email", {"type": "email", "to": "test@example.com", "subject": "Alert Test", "timestamp": "2026-03-16T10:00:00Z"})
        ]
        
        for channel, payload in test_messages:
            json_payload = json.dumps(payload)
            print(f"Publishing to Redis channel {channel}...")
            await redis.publish(channel, json_payload)
            
            # Wait for WS message
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                received = json.loads(msg)
                print(f"Received via WS: {received}")
                
                # Simple verification
                if "ticker" in received and received["ticker"] == payload.get("ticker"):
                    print(f"SUCCESS: Received correct price/forecast data for {channel}")
                elif "symbol" in received and received["symbol"] == payload.get("symbol"):
                    print(f"SUCCESS: Received correct sentiment data for {channel}")
                elif "type" in received and received["type"] == payload.get("type"):
                    print(f"SUCCESS: Received correct alert data for {channel}")
                else:
                    print(f"WARNING: Received unexpected payload structure: {received}")
            except asyncio.TimeoutError:
                print(f"FAILURE: Timeout waiting for message from {channel}")
                
    await redis.close()
    print("--- Test Completed ---")

if __name__ == "__main__":
    try:
        asyncio.run(test_ws_integration())
    except Exception as e:
        print(f"Error during test: {e}")
