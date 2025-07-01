#!/usr/bin/env python

import asyncio
import websockets
import os
import json
import sys
from typing import AsyncGenerator, Dict, Any
from pathlib import Path

# LangChain imports
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain_together import ChatTogether

# Import the attendance function
from get_attendance import get_student_attendance

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

def attendance_tool_func(input_str: str) -> str:
    """
    Tool function to get student attendance data.
    Expected input format: "student_id,password" or JSON string with student_id and password
    """
    try:
        # Try parsing as JSON first
        try:
            data = json.loads(input_str)
            student_id = data.get('student_id')
            password = data.get('password')
        except json.JSONDecodeError:
            # Fallback to comma-separated format
            parts = input_str.split(',', 1)
            if len(parts) != 2:
                return "❌ Please provide student ID and password in format: student_id,password"
            student_id, password = parts[0].strip(), parts[1].strip()
        
        if not student_id or not password:
            return "❌ Both student ID and password are required"
        
        # Get attendance data
        result = get_student_attendance(student_id, password)
        
        # Return user-friendly response based on result
        if result.get('success'):
            summary = result.get('summary', {})
            overall_percentage = summary.get('overall_percentage', 0)
            
            response = f"✅ {result.get('message', '')}\n\n"
            
            # Add subject breakdown if available
            subjects = summary.get('subjects', {})
            if subjects:
                response += "📚 Subject-wise Attendance:\n"
                for subject_code, subject_info in subjects.items():
                    name = subject_info.get('course_name', subject_code)
                    percentage = subject_info.get('percentage', 0)
                    present = subject_info.get('total_present', 0)
                    total = subject_info.get('total_classes', 0)
                    
                    status = "⚠️" if percentage < 75 else "✅"
                    response += f"{status} {name}: {percentage:.1f}% ({present}/{total})\n"
                
                response += f"\n🎯 Overall Attendance: {overall_percentage}%"
                
                # Add warning for low attendance
                low_subjects = [s for s in subjects.values() if s.get('percentage', 0) < 75]
                if low_subjects:
                    response += f"\n\n⚠️ Warning: {len(low_subjects)} subject(s) below 75% attendance threshold"
            else:
                response += f"🎯 Overall Attendance: {overall_percentage}%"
            
            return response
        else:
            return f"❌ {result.get('message', 'Failed to retrieve attendance data')}"
        
    except Exception as e:
        return f"❌ Error retrieving attendance: {str(e)}"

class TogetherAIBackend:
    def __init__(self):
        self.api_key = os.getenv('TOGETHER_API_KEY')
        self.model = os.getenv('TOGETHER_MODEL', 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo')
        
        if not self.api_key:
            print("❌ TOGETHER_API_KEY environment variable not set!")
            print("Please set your Together.AI API key:")
            print("export TOGETHER_API_KEY='your-api-key-here'")
            sys.exit(1)
        
        # Initialize LangChain ChatTogether
        self.llm = ChatTogether(
            api_key=self.api_key,
            model=self.model,
            temperature=0.7,
            max_tokens=512
        )
        
        # Define the attendance tool
        self.attendance_tool = Tool(
            name="get_attendance",
            description="""Get student attendance data from CHARUSAT portal. 
            ONLY use this tool when the user has provided BOTH their student ID and password.
            Input format: {"student_id": "23CS012", "password": "user_password"}
            DO NOT use this tool if the user hasn't provided credentials.
            This tool returns complete attendance information - do not call it again.""",
            func=attendance_tool_func,
            return_direct=True  # Prevents agent from processing tool output further
        )
        
        # Create agent with tools
        self.tools = [self.attendance_tool]
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant for CHARUSAT students. You can help with general questions and check attendance data.

IMPORTANT RULES:
1. For general conversation, respond normally without using tools
2. For attendance requests, ONLY use the get_attendance tool when BOTH student ID and password are provided
3. Use the get_attendance tool ONLY ONCE per request - it returns complete information
4. DO NOT call tools repeatedly or try to "improve" tool outputs
5. Present tool results clearly and conversationally

When a user asks for attendance:
- If they haven't provided credentials, ask for student ID and password
- If they have provided both, use the tool once and present the results
- Do not call the tool again to "verify" or "get more details"

Be helpful, friendly, and efficient."""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=False,
            max_iterations=2,  # Reduced to prevent loops
            return_intermediate_steps=True,
            early_stopping_method="generate"  # Stop after first tool call if return_direct=True
        )
        
        print(f"✅ Together.AI with LangChain initialized with model: {self.model}")
    
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Stream chat completion using LangChain agent"""
        try:
            # Check if this is a simple greeting
            message_lower = message.lower().strip()
            simple_greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
            
            if any(greeting in message_lower for greeting in simple_greetings) and len(message.split()) <= 3:
                # Handle simple greetings without using the agent
                response = f"Hello! I'm your CHARUSAT assistant. I can help you with general questions or check your attendance data. How can I assist you today?"
                words = response.split()
                for i, word in enumerate(words):
                    yield word + (" " if i < len(words) - 1 else "")
                    await asyncio.sleep(0.03)
                return
            
            # Run the agent - it will handle tool calls automatically
            agent_response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.agent_executor.invoke({"input": message})
            )
            
            # Get the output (will be tool output if return_direct=True was used)
            output = agent_response.get("output", "I'm sorry, I couldn't process your request. Please try again.")
            
            # Stream the response word by word for better UX
            words = output.split()
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                await asyncio.sleep(0.03)
                
        except Exception as e:
            print(f"❌ Error in chat_stream: {e}")
            yield f"I'm sorry, I encountered an error. Please try again."

# Global Together.AI instance
together_ai = TogetherAIBackend()

async def handle_chat(websocket):
    """Handle WebSocket chat messages"""
    try:
        async for message in websocket:
            print(f"📨 Received: {message}", flush=True)
            
            # Stream response from Together.AI with LangChain
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
    
    print("🚀 Together.AI WebSocket Server with LangChain Starting...")
    print(f"🌐 Server will run on port {port}")
    print(f"🤖 Using model: {together_ai.model}")
    print("🛠️  Available tools: get_attendance")
    
    async with websockets.serve(
        handle_chat,
        "0.0.0.0",
        port
    ) as server:
        print(f"✅ WebSocket server running on port {port}")
        print("🔗 Connect your frontend to this server")
        print("📚 Students can now ask for their attendance!")
        print("⏹️  Press Ctrl+C to stop")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
