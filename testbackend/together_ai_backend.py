#!/usr/bin/env python

import asyncio
import websockets
import os
import json
import aiohttp
import sys
from typing import AsyncGenerator
from pathlib import Path

# Load environment variables from .env file if it exists
def load_env():
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

class TogetherAIBackend:
    def __init__(self):
        self.api_key = os.getenv('TOGETHER_API_KEY')
        self.base_url = "https://api.together.xyz/v1/chat/completions"
        self.model = os.getenv('TOGETHER_MODEL', 'meta-llama/Llama-2-7b-chat-hf')
        
        if not self.api_key:
            print("❌ TOGETHER_API_KEY environment variable not set!")
            print("Please set your Together.AI API key:")
            print("export TOGETHER_API_KEY='your-api-key-here'")
            sys.exit(1)
        
        print(f"✅ Together.AI initialized with model: {self.model}")
    
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Stream chat completion from Together.AI"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful, knowledgeable, and friendly AI assistant. Provide clear, concise, and accurate responses."
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            "stream": True,
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ API Error {response.status}: {error_text}")
                        yield f"❌ API Error: {response.status} - {error_text}"
                        return
                    
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]  # Remove 'data: ' prefix
                                
                                if data_str == '[DONE]':
                                    break
                                
                                try:
                                    data = json.loads(data_str)
                                    if 'choices' in data and len(data['choices']) > 0:
                                        delta = data['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            content = delta['content']
                                            if content:
                                                yield content
                                except json.JSONDecodeError:
                                    continue
                    
        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}")
            yield f"❌ Connection error: {str(e)}"
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            yield f"❌ Unexpected error: {str(e)}"

# Global Together.AI instance
together_ai = TogetherAIBackend()

async def handle_chat(websocket):
    """Handle WebSocket chat messages"""
    try:
        async for message in websocket:
            print(f"📨 Received: {message}", flush=True)
            
            # Stream response from Together.AI
            async for chunk in together_ai.chat_stream(message):
                if chunk:  # Only send non-empty chunks
                    await websocket.send(chunk)
            
            # Send end marker
            await websocket.send("[END]")
            print("✅ Response completed", flush=True)
            
    except websockets.exceptions.ConnectionClosed:
        print("👋 Client disconnected", flush=True)
    except Exception as e:
        print(f"❌ Error in chat handler: {e}", flush=True)

async def main():
    """Main server function"""
    port = int(os.environ.get('PORT', 8092))
    
    print("🚀 Together.AI WebSocket Server Starting...")
    print(f"🌐 Server will run on port {port}")
    print(f"🤖 Using model: {together_ai.model}")
    
    async with websockets.serve(
        handle_chat,
        "0.0.0.0",
        port
    ) as server:
        print(f"✅ WebSocket server running on port {port}")
        print("🔗 Connect your frontend to this server")
        print("⏹️  Press Ctrl+C to stop")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
