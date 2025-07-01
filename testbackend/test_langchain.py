#!/usr/bin/env python3
"""
Test script for the LangChain integration with attendance tool
"""

import os
import json
from together_ai_backend import TogetherAIBackend

def test_attendance_tool():
    """Test the attendance tool directly"""
    
    # Set up environment (you'll need to set your API key)
    if not os.getenv('TOGETHER_API_KEY'):
        print("❌ Please set TOGETHER_API_KEY environment variable")
        return
    
    print("🧪 Testing LangChain integration...")
    
    try:
        # Initialize backend
        backend = TogetherAIBackend()
        print("✅ Backend initialized successfully")
        
        # Test the attendance tool directly
        print("\n🛠️ Testing attendance tool...")
        test_input = '{"student_id": "test123", "password": "testpass"}'
        result = backend.attendance_tool.func(test_input)
        print(f"Tool result: {result}")
        
        print("\n✅ LangChain integration test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_attendance_tool()
