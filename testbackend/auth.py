#!/usr/bin/env python

import sqlite3
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Dict, Any
import json

class AuthManager:
    def __init__(self):
        self.db_path = Path(__file__).parent / 'auth.db'
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                student_id TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                egov_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_session_id(self) -> str:
        """Generate a secure session ID"""
        return secrets.token_urlsafe(32)
    
    def verify_egov_credentials(self, student_id: str, egov_password: str) -> Dict[str, Any]:
        """Verify e-governance credentials by checking if login succeeds"""
        try:
            print(f"🔐 Verifying e-governance credentials for: {student_id}")
            
            # Import here to avoid circular imports
            from get_attendance import create_session, login_to_portal
            
            # Create session and try to login
            session = create_session()
            dashboard_html = login_to_portal(session, student_id, egov_password)
            
            if dashboard_html:
                print(f"✅ E-governance credentials verified successfully")
                return {
                    'success': True,
                    'message': 'E-governance credentials verified successfully'
                }
            else:
                print(f"❌ E-governance verification failed: Invalid credentials")
                return {
                    'success': False,
                    'message': 'Invalid e-governance credentials'
                }
                
        except Exception as e:
            print(f"❌ E-governance verification error: {str(e)}")
            return {
                'success': False,
                'message': f'Verification failed: {str(e)}'
            }
    
    def register_user(self, username: str, student_id: str, password: str, egov_password: str) -> Dict[str, Any]:
        """Register a new user with e-governance credential verification"""
        try:
            # First verify e-governance credentials
            print(f"🔐 Verifying e-governance credentials for student: {student_id}")
            
            verification_result = self.verify_egov_credentials(student_id, egov_password)
            
            if not verification_result.get('success'):
                print(f"❌ E-governance verification failed: {verification_result.get('message', 'Unknown error')}")
                return {
                    'success': False, 
                    'message': f"E-governance credential verification failed: {verification_result.get('message', 'Invalid student ID or password')}"
                }
            
            print(f"✅ E-governance credentials verified successfully")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'message': 'Username already exists'}
            
            # Check if student_id already exists
            cursor.execute('SELECT id FROM users WHERE student_id = ?', (student_id,))
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'message': 'Student ID already registered'}
            
            # Hash the login password
            password_hash = self.hash_password(password)
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, student_id, password_hash, egov_password)
                VALUES (?, ?, ?, ?)
            ''', (username, student_id, password_hash, egov_password))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True, 
                'message': 'User registered successfully with verified e-governance credentials',
                'user_id': user_id
            }
            
        except Exception as e:
            print(f"❌ Registration error: {str(e)}")
            return {'success': False, 'message': f'Registration failed: {str(e)}'}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login a user and create a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user by username
            cursor.execute('''
                SELECT id, username, student_id, password_hash, egov_password 
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return {'success': False, 'message': 'Invalid username or password'}
            
            user_id, username, student_id, stored_hash, egov_password = user
            
            # Verify password
            if self.hash_password(password) != stored_hash:
                conn.close()
                return {'success': False, 'message': 'Invalid username or password'}
            
            # Create session
            session_id = self.generate_session_id()
            cursor.execute('''
                INSERT INTO sessions (session_id, user_id)
                VALUES (?, ?)
            ''', (session_id, user_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Login successful',
                'session_id': session_id,
                'user': {
                    'username': username,
                    'student_id': student_id,
                    'egov_password': egov_password
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Login failed: {str(e)}'}
    
    def get_user_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user details by session ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.student_id, u.egov_password
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.session_id = ?
            ''', (session_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'student_id': user[2],
                    'egov_password': user[3]
                }
            return None
            
        except Exception as e:
            print(f"Error getting user by session: {e}")
            return None
    
    def logout_user(self, session_id: str) -> bool:
        """Logout a user by removing their session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error logging out user: {e}")
            return False
