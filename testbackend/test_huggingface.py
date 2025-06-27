#!/usr/bin/env python

import asyncio
import websockets
import os
import json
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import threading
from queue import Queue

class LocalLLMBackend:
    def __init__(self, model_name="distilgpt2"):  # Using lightweight distilgpt2 for testing
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        print(f"Selected model: {self.model_name} (lightweight for testing)")
        
    async def initialize_model(self):
        """Initialize the model in a separate thread to avoid blocking"""
        print(f"Loading model: {self.model_name}")
        
        try:
            # Use text generation pipeline for simplicity
            print("Initializing text generation pipeline...")
            self.generator = pipeline(
                "text-generation",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                max_length=512,  # Limit max length for faster inference
            )
            
            print(f"✅ Model '{self.model_name}' loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading model {self.model_name}: {e}")
            # Fallback to the smallest possible model
            print("🔄 Falling back to distilgpt2...")
            try:
                self.model_name = "distilgpt2"
                self.generator = pipeline("text-generation", model="distilgpt2", max_length=256)
                print("✅ Fallback model loaded successfully!")
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                self.generator = None
    
    async def generate_response(self, message, max_new_tokens=50):
        """Generate response using the loaded model"""
        try:
            if not self.generator:
                return "❌ Model not available. Please restart the server."
            
            # Create a simple prompt for text generation
            prompt = f"User: {message}\nAssistant:"
            
            # Generate response
            result = self.generator(
                prompt,
                max_new_tokens=max_new_tokens,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.generator.tokenizer.eos_token_id,
                eos_token_id=self.generator.tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )
            
            response = result[0]['generated_text']
            
            # Extract only the assistant's response
            if "Assistant:" in response:
                response = response.split("Assistant:")[-1].strip()
            else:
                response = response[len(prompt):].strip()
            
            # Clean up the response
            response = response.split("User:")[0].strip()  # Stop at next user message
            response = response.split("\n")[0].strip()     # Take first line only
            
            return response if response else "I'm thinking..."
                
        except Exception as e:
            return f"❌ Error generating response: {str(e)}"

# Global model instance
llm_backend = LocalLLMBackend()

async def handle_chat(websocket):
    try:
        async for message in websocket:
            print(f"Received message: {message}", flush=True)
            
            # Generate response
            response = await llm_backend.generate_response(message)
            
            # Send response in chunks to simulate streaming
            words = response.split()
            for i, word in enumerate(words):
                if i == 0:
                    await websocket.send(word)
                else:
                    await websocket.send(" " + word)
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send end marker
            await websocket.send("[END]")
            
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

async def main():
    print("Initializing Local LLM Backend...")
    await llm_backend.initialize_model()
    
    print("WebSocket server starting", flush=True)
    
    async with websockets.serve(
        handle_chat,
        "0.0.0.0",
        int(os.environ.get('PORT', 8091))
    ) as server:
        print("WebSocket server running on port 8091", flush=True)
        print("Local LLM backend ready!", flush=True)
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
