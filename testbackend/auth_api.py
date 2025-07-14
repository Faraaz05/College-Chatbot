#!/usr/bin/env python

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
from auth import AuthManager

app = FastAPI(title="CHARUSAT Chatbot Auth API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize auth manager
auth_manager = AuthManager()

# Pydantic models
class RegisterRequest(BaseModel):
    username: str
    student_id: str
    password: str
    egov_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    user: Optional[dict] = None

@app.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    result = auth_manager.register_user(
        username=request.username,
        student_id=request.student_id,
        password=request.password,
        egov_password=request.egov_password
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return AuthResponse(
        success=result['success'],
        message=result['message']
    )

@app.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login a user"""
    result = auth_manager.login_user(
        username=request.username,
        password=request.password
    )
    
    if not result['success']:
        raise HTTPException(status_code=401, detail=result['message'])
    
    return AuthResponse(
        success=result['success'],
        message=result['message'],
        session_id=result['session_id'],
        user=result['user']
    )

@app.get("/me")
async def get_current_user(request: Request):
    """Get current user by session ID"""
    session_id = request.headers.get("Authorization")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session provided")
    
    # Remove "Bearer " prefix if present
    if session_id.startswith("Bearer "):
        session_id = session_id[7:]
    
    user = auth_manager.get_user_by_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return {"success": True, "user": user}

@app.post("/logout")
async def logout(request: Request):
    """Logout a user"""
    session_id = request.headers.get("Authorization")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session provided")
    
    # Remove "Bearer " prefix if present
    if session_id.startswith("Bearer "):
        session_id = session_id[7:]
    
    success = auth_manager.logout_user(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Logout failed")
    
    return {"success": True, "message": "Logged out successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth"}

if __name__ == "__main__":
    port = int(os.environ.get('AUTH_PORT', 8093))
    print(f"🚀 Starting Auth API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
