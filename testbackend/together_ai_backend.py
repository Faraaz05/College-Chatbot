#!/usr/bin/env python

import asyncio
import websockets
import os
import json
import sys
from typing import AsyncGenerator, Dict, Any
from pathlib import Path

# LangChain imports
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate
from langchain_together import ChatTogether

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Import the attendance function
from get_attendance import get_student_attendance

# Import authentication
from auth import AuthManager

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

def attendance_tool_func(session_id: str = None) -> str:
    """
    Tool function to get student attendance data using session-based authentication.
    """
    try:
        if not session_id:
            return "❌ You need to be logged in to check attendance. Please log in first."
        
        # Get auth manager instance
        auth_manager = AuthManager()
        user = auth_manager.get_user_by_session(session_id)
        
        if not user:
            return "❌ Invalid session. Please log in again."
        
        student_id = user['student_id']
        password = user['egov_password']
        
        if not student_id or not password:
            return "❌ Missing credentials in your profile"
        
        result = get_student_attendance(student_id, password)
        if result.get('success'):
            summary = result.get('summary', {})
            overall_percentage = summary.get('overall_percentage', 0)
            response = f"✅ {result.get('message', '')}\n\n"
            subjects = summary.get('subjects', {})
            if subjects:
                response += "📚 Subject-wise Attendance:\n"
                for subject_key, subject_info in subjects.items():
                    name = subject_info.get('course_name', subject_key)
                    percentage = subject_info.get('percentage', 0)
                    present = subject_info.get('total_present', 0)
                    total = subject_info.get('total_classes', 0)
                    status = "⚠️" if percentage < 75 else "✅"
                    response += f"{status} {name}: {percentage:.1f}% ({present}/{total})\n"
                response += f"\n🎯 Overall Attendance: {overall_percentage}%"
                low_subjects = [s for s in subjects.values() if s.get('percentage', 0) < 75]
                if low_subjects:
                    response += f"\n\n⚠️ Warning: {len(low_subjects)} subject(s) below 75% attendance threshold"
            else:
                response += f"🎯 Overall Attendance: {overall_percentage}%"
            print("________________________________________")
            print(response)
            return response
        else:
            return f"❌ {result.get('message', 'Failed to retrieve attendance data')}"
    except Exception as e:
        return f"❌ Error retrieving attendance: {str(e)}"

# Define the state for our graph
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    tool_call_count: int

class TogetherAIBackend:
    def __init__(self):
        self.api_key = os.getenv('TOGETHER_API_KEY')
        self.model = os.getenv('TOGETHER_MODEL', 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo')
        
        # Conversation memory to store chat history
        self.conversation_history = []
        
        # Current user session
        self.current_session_id = None
        
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
        self.attendance_tool = StructuredTool.from_function(
            func=self.get_attendance_with_session,
            name="get_attendance",
            description="""Get student attendance data from CHARUSAT portal using stored credentials.
            ONLY use this tool when the user asks for their attendance and they are logged in.
            This tool automatically uses the logged-in user's credentials."""
        )
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools([self.attendance_tool])
        
        # Create the workflow graph
        self.workflow = StateGraph(AgentState)
        
        # Add nodes
        self.workflow.add_node("agent", self.call_model)
        self.workflow.add_node("tools", self.call_tools)
        
        # Add edges
        self.workflow.set_entry_point("agent")
        self.workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )
        self.workflow.add_edge("tools", "agent")  # After tools, go back to agent for final response
        
        # Compile the graph
        self.app = self.workflow.compile()
        
        print(f"✅ Together.AI with LangGraph initialized with model: {self.model}")
    
    def call_model(self, state: AgentState):
        """Call the LLM with system prompt"""
        messages = state['messages']
        
        # Create a proper conversation with system message and history
        conversation = []
        
        # Add system message
        system_msg = f"System: {self.get_system_prompt()}"
        conversation.append(HumanMessage(content=system_msg))
        
        # Add conversation history (previous messages)
        for hist_msg in self.conversation_history:
            conversation.append(hist_msg)
        
        # Add current messages
        for msg in messages:
            conversation.append(msg)
        
        response = self.llm_with_tools.invoke(conversation)
        return {"messages": [response]}
    
    def call_tools(self, state: AgentState):
        """Execute tool calls"""
        messages = state['messages']
        last_message = messages[-1]
        
        tool_outputs = []
        for tool_call in last_message.tool_calls:
            tool_output = self.attendance_tool.invoke(tool_call["args"])
            tool_outputs.append(
                ToolMessage(
                    content=tool_output,
                    tool_call_id=tool_call["id"]
                )
            )
        
        return {"messages": tool_outputs, "tool_call_count": state.get('tool_call_count', 0) + 1}
    
    def should_continue(self, state: AgentState):
        """Decide whether to continue to tools or end"""
        messages = state['messages']
        last_message = messages[-1]
        tool_call_count = state.get('tool_call_count', 0)
        
        # If we've already made a tool call, don't make another one
        if tool_call_count >= 1:
            return "end"
        
        # If there are tool calls, go to tools
        if last_message.tool_calls:
            return "continue"
        # Otherwise, we're done
        return "end"
    
    def get_system_prompt(self):
        """Get the system prompt"""
        session_status = "logged in" if self.current_session_id else "not logged in"
        return f"""You are a helpful, friendly, and knowledgeable AI assistant for CHARUSAT students. You are a general-purpose college chatbot: you can answer questions about college life, academics, events, procedures, and more, as well as check attendance data.

CURRENT USER STATUS: The user is {session_status}.

IMPORTANT RULES:
1. For general conversation or college-related questions, respond normally without using tools.
2. For attendance requests, use the get_attendance tool ONLY if the user is logged in.
3. If user asks for attendance and they are logged in, use the tool and present the results.
4. If user asks for attendance but they are not logged in, tell them they need to register/login first.
5. Use the get_attendance tool ONLY ONCE per request - it returns complete information.
6. After using the get_attendance tool, provide a friendly interpretation of the results.
7. For follow-up questions about previously retrieved attendance data, use the information from our conversation history. DO NOT call the tool again.
8. Present tool results clearly and conversationally.

When a user asks for attendance:
- If they are not logged in, tell them to log in first at /login
- If they are logged in, use the tool once and present the results
- For follow-up questions about the same attendance data, refer to the previous tool output in our conversation

For all other questions, answer as a helpful college chatbot.

Be helpful, friendly, and efficient."""
    
    def set_session(self, session_id: str):
        """Set the current session ID"""
        self.current_session_id = session_id
    
    def get_attendance_with_session(self) -> str:
        """Wrapper function to call attendance_tool_func with current session"""
        return attendance_tool_func(self.current_session_id)
    
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Stream chat completion using LangGraph agent"""
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
            
            # Create human message
            human_message = HumanMessage(content=message)
            
            # Run the graph
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.app.invoke({"messages": [human_message], "tool_call_count": 0})
            )
            
            # Get the final response
            final_messages = result["messages"]
            output = ""
            
            if final_messages:
                # Get the last AI message
                for msg in reversed(final_messages):
                    if isinstance(msg, AIMessage) and not msg.tool_calls:
                        output = msg.content
                        break
                    elif isinstance(msg, ToolMessage):
                        # If we only have tool output, use that
                        output = msg.content
                        break
                else:
                    output = "I'm sorry, I couldn't process your request. Please try again."
            else:
                output = "I'm sorry, I couldn't process your request. Please try again."
            
            # Store conversation in memory for follow-up questions
            self.conversation_history.append(human_message)
            
            # Store all messages from this conversation (including tool calls/outputs)
            for msg in final_messages:
                if isinstance(msg, (AIMessage, ToolMessage)):
                    self.conversation_history.append(msg)
            
            # Keep only last 10 messages to prevent context overflow
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            # Stream the response preserving formatting with chunks
            # Split by lines and send meaningful chunks
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if line.strip():  # Only process non-empty lines
                    # For structured data (like attendance), send line by line
                    # For regular text, send word by word
                    if any(symbol in line for symbol in ['✅', '⚠️', '📚', '🎯', '%', '(']):
                        # This looks like structured attendance data - send the whole line
                        yield line
                        await asyncio.sleep(0.1)
                    else:
                        # Regular text - send word by word
                        words = line.split()
                        for j, word in enumerate(words):
                            yield word + (" " if j < len(words) - 1 else "")
                            await asyncio.sleep(0.03)
                # Send line break after each line (except the last one)
                if i < len(lines) - 1:
                    yield "\n"
                    await asyncio.sleep(0.03)
                
        except Exception as e:
            print(f"❌ Error in chat_stream: {e}")
            yield f"I'm sorry, I encountered an error. Please try again."

# Global Together.AI instance
together_ai = TogetherAIBackend()

async def handle_chat(websocket):
    """Handle WebSocket chat messages"""
    try:
        # Get session ID from query parameters if available
        session_id = None
        
        async for message in websocket:
            # Check if this is a session setup message
            if message.startswith("SESSION:"):
                session_id = message.replace("SESSION:", "")
                together_ai.set_session(session_id)
                continue
            
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
