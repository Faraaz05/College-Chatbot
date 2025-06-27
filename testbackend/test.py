#!/usr/bin/env python

import asyncio
import websockets
import os
import json
import aiohttp
import sys

async def chat_with_ollama(message, model="llama3.2"):
    """Send message to Ollama and get streaming response"""
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user", 
                "content": message
            }
        ],
        "stream": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'message' in data and 'content' in data['message']:
                                    yield data['message']['content']
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    yield f"Error: Ollama server returned status {response.status}"
    except aiohttp.ClientError as e:
        yield f"Error connecting to Ollama: {str(e)}"
    except Exception as e:
        yield f"Unexpected error: {str(e)}"

async def handle_chat(websocket):
    try:
        async for message in websocket:
            print(f"Received message: {message}", flush=True)
            
            # Stream response from Ollama
            async for chunk in chat_with_ollama(message):
                if chunk:  # Only send non-empty chunks
                    await websocket.send(chunk)
            
            # Send end marker
            await websocket.send("[END]")
            
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

async def main():
    print("WebSocket server starting", flush=True)
    
    # Create the server with CORS headers
    async with websockets.serve(
        handle_chat,
        "0.0.0.0",
        int(os.environ.get('PORT', 8090))
    ) as server:
        print("WebSocket server running on port 8090", flush=True)
        print("Make sure Ollama is running on http://localhost:11434", flush=True)
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())