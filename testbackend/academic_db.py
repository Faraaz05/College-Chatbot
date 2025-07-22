#!/usr/bin/env python3
"""
Academic Database Module for CHARUSAT College Chatbot
Handles faculty, subjects, and counsellor information queries
"""

import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class AcademicDatabase:
    def __init__(self):
        self.db_path = Path(__file__).parent / 'academic.db'
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with academic tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create Faculty table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Faculty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                department TEXT,
                designation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create Subject table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Subject (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                semester INTEGER,
                year INTEGER,
                branch TEXT,
                description TEXT,
                credits INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create FacultySubjectMap table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS FacultySubjectMap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_id INTEGER,
                subject_id INTEGER,
                academic_year TEXT,
                FOREIGN KEY(faculty_id) REFERENCES Faculty(id),
                FOREIGN KEY(subject_id) REFERENCES Subject(id),
                UNIQUE(faculty_id, subject_id, academic_year)
            )
        ''')
        
        # Create Counsellor table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Counsellor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                branch TEXT,
                roll_range_start TEXT,
                roll_range_end TEXT,
                academic_year TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject_name ON Subject(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject_code ON Subject(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject_branch_year ON Subject(branch, year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_faculty_name ON Faculty(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_counsellor_branch ON Counsellor(branch)')
        
        conn.commit()
        conn.close()
        print("✅ Academic database initialized successfully")
    
    def calculate_year_from_roll(self, roll_number: str) -> int:
        """Calculate current academic year from roll number"""
        try:
            # Extract year from roll number (e.g., "23CS045" -> 23)
            year_match = re.match(r'(\d{2})', roll_number)
            if year_match:
                admission_year = int(year_match.group(1))
                current_year = datetime.now().year % 100  # Get last 2 digits of current year
                
                # Calculate academic year (1st, 2nd, 3rd, 4th)
                academic_year = current_year - admission_year + 1
                return max(1, min(4, academic_year))  # Clamp between 1-4
            return 1
        except:
            return 1
    
    def extract_branch_from_roll(self, roll_number: str) -> str:
        """Extract branch from roll number"""
        try:
            # Extract branch from roll number (e.g., "23CS045" -> "CS")
            branch_match = re.search(r'\d{2}([A-Z]+)', roll_number)
            if branch_match:
                return branch_match.group(1)
            return "CS"  # Default to CS
        except:
            return "CS"
    
    def fuzzy_match_subject(self, subject_query: str) -> List[str]:
        """Find subjects that match the query with fuzzy matching"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Common abbreviations and their full forms
        abbreviations = {
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'ds': 'data structures',
            'dsa': 'data structures and algorithms',
            'os': 'operating system',
            'dbms': 'database management system',
            'cn': 'computer networks',
            'se': 'software engineering',
            'oop': 'object oriented programming',
            'java': 'java programming',
            'python': 'python programming',
            'web': 'web development',
            'mobile': 'mobile application development',
            'android': 'android development'
        }
        
        query_lower = subject_query.lower().strip()
        
        # Check if it's a common abbreviation
        if query_lower in abbreviations:
            expanded_query = abbreviations[query_lower]
        else:
            expanded_query = query_lower
        
        # Search with multiple patterns
        search_patterns = [
            f"%{expanded_query}%",
            f"%{query_lower}%",
            f"{query_lower}%",
            f"%{query_lower}"
        ]
        
        subjects = []
        for pattern in search_patterns:
            cursor.execute('''
                SELECT DISTINCT code, name FROM Subject 
                WHERE LOWER(name) LIKE ? OR LOWER(code) LIKE ?
                ORDER BY 
                    CASE 
                        WHEN LOWER(name) = ? THEN 1
                        WHEN LOWER(name) LIKE ? THEN 2
                        WHEN LOWER(code) = ? THEN 3
                        ELSE 4
                    END
                LIMIT 10
            ''', (pattern, pattern, query_lower, f"{query_lower}%", query_lower.upper()))
            
            results = cursor.fetchall()
            for code, name in results:
                if (code, name) not in [(s['code'], s['name']) for s in subjects]:
                    subjects.append({'code': code, 'name': name})
        
        conn.close()
        return subjects
    
    def get_faculty_by_subject(self, subject_name: str) -> List[Dict]:
        """Get faculty teaching a specific subject"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, find matching subjects
            matching_subjects = self.fuzzy_match_subject(subject_name)
            
            if not matching_subjects:
                return []
            
            faculty_list = []
            for subject in matching_subjects:
                cursor.execute('''
                    SELECT DISTINCT f.name, f.email, f.phone, f.department, f.designation, s.name as subject_name, s.code
                    FROM Faculty f
                    JOIN FacultySubjectMap fsm ON f.id = fsm.faculty_id
                    JOIN Subject s ON fsm.subject_id = s.id
                    WHERE s.code = ? OR LOWER(s.name) LIKE LOWER(?)
                    ORDER BY f.name
                ''', (subject['code'], f"%{subject['name']}%"))
                
                results = cursor.fetchall()
                for row in results:
                    faculty_info = {
                        'name': row[0],
                        'email': row[1] or 'Not available',
                        'phone': row[2] or 'Not available',
                        'department': row[3] or 'Not specified',
                        'designation': row[4] or 'Faculty',
                        'subject_name': row[5],
                        'subject_code': row[6]
                    }
                    # Avoid duplicates
                    if not any(f['name'] == faculty_info['name'] and f['subject_code'] == faculty_info['subject_code'] for f in faculty_list):
                        faculty_list.append(faculty_info)
            
            conn.close()
            return faculty_list
            
        except Exception as e:
            print(f"❌ Error getting faculty by subject: {e}")
            return []
    
    def get_subjects_by_year_and_branch(self, year: int, branch: str) -> List[Dict]:
        """Get subjects for a specific year and branch"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT code, name, semester, credits, description
                FROM Subject
                WHERE year = ? AND UPPER(branch) = UPPER(?)
                ORDER BY semester, name
            ''', (year, branch))
            
            results = cursor.fetchall()
            subjects = []
            for row in results:
                subjects.append({
                    'code': row[0],
                    'name': row[1],
                    'semester': row[2] or 'Not specified',
                    'credits': row[3] or 'Not specified',
                    'description': row[4] or 'No description available'
                })
            
            conn.close()
            return subjects
            
        except Exception as e:
            print(f"❌ Error getting subjects by year and branch: {e}")
            return []
    
    def get_counsellor_by_roll(self, roll_number: str) -> Optional[Dict]:
        """Get counsellor information for a student roll number"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract branch from roll number
            branch = self.extract_branch_from_roll(roll_number)
            
            cursor.execute('''
                SELECT name, email, phone, branch, roll_range_start, roll_range_end
                FROM Counsellor
                WHERE UPPER(branch) = UPPER(?) 
                AND ? BETWEEN roll_range_start AND roll_range_end
                ORDER BY roll_range_start
            ''', (branch, roll_number))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'name': result[0],
                    'email': result[1] or 'Not available',
                    'phone': result[2] or 'Not available',
                    'branch': result[3],
                    'roll_range': f"{result[4]} to {result[5]}"
                }
            return None
            
        except Exception as e:
            print(f"❌ Error getting counsellor by roll: {e}")
            return None
    
    def format_faculty_response(self, faculty_list: List[Dict], subject_name: str) -> str:
        """Format faculty information as a friendly response"""
        if not faculty_list:
            return f"❌ Sorry, I couldn't find any faculty teaching '{subject_name}'. Please check the subject name or try a different search term."
        
        response = f"👨‍🏫 **Faculty teaching '{subject_name}':**\n\n"
        
        # Group by subject if multiple subjects found
        subjects_found = set(f['subject_name'] for f in faculty_list)
        
        if len(subjects_found) > 1:
            response += f"Found {len(subjects_found)} related subjects:\n\n"
            
            for subject in subjects_found:
                subject_faculty = [f for f in faculty_list if f['subject_name'] == subject]
                response += f"📚 **{subject}**\n"
                for faculty in subject_faculty:
                    response += f"   • **{faculty['name']}** ({faculty['designation']})\n"
                    if faculty['email'] != 'Not available':
                        response += f"     📧 {faculty['email']}\n"
                    if faculty['phone'] != 'Not available':
                        response += f"     📞 {faculty['phone']}\n"
                response += "\n"
        else:
            subject = list(subjects_found)[0]
            response += f"📚 **{subject}**\n\n"
            for faculty in faculty_list:
                response += f"👨‍🏫 **{faculty['name']}** - {faculty['designation']}\n"
                response += f"   🏢 Department: {faculty['department']}\n"
                if faculty['email'] != 'Not available':
                    response += f"   📧 Email: {faculty['email']}\n"
                if faculty['phone'] != 'Not available':
                    response += f"   📞 Phone: {faculty['phone']}\n"
                response += "\n"
        
        return response.strip()
    
    def format_subjects_response(self, subjects: List[Dict], year: int, branch: str) -> str:
        """Format subjects information as a friendly response"""
        if not subjects:
            return f"❌ Sorry, I couldn't find any subjects for {year}{'st' if year == 1 else 'nd' if year == 2 else 'rd' if year == 3 else 'th'} year {branch} students."
        
        year_suffix = 'st' if year == 1 else 'nd' if year == 2 else 'rd' if year == 3 else 'th'
        response = f"📚 **{year}{year_suffix} Year {branch} Subjects:**\n\n"
        
        # Group by semester
        semesters = {}
        for subject in subjects:
            sem = subject['semester']
            if sem not in semesters:
                semesters[sem] = []
            semesters[sem].append(subject)
        
        for semester in sorted(semesters.keys()):
            if semester != 'Not specified':
                response += f"**Semester {semester}:**\n"
            else:
                response += f"**General Subjects:**\n"
            
            for subject in semesters[semester]:
                response += f"   • **{subject['code']}** - {subject['name']}"
                if subject['credits'] != 'Not specified':
                    response += f" ({subject['credits']} credits)"
                response += "\n"
                if subject['description'] != 'No description available':
                    response += f"     ℹ️ {subject['description']}\n"
            response += "\n"
        
        response += f"📊 **Total Subjects:** {len(subjects)}"
        return response.strip()
    
    def format_counsellor_response(self, counsellor: Optional[Dict], roll_number: str) -> str:
        """Format counsellor information as a friendly response"""
        if not counsellor:
            branch = self.extract_branch_from_roll(roll_number)
            return f"❌ Sorry, I couldn't find a counsellor assigned for roll number '{roll_number}' in {branch} branch. Please contact the academic office."
        
        response = f"👨‍💼 **Your Student Counsellor:**\n\n"
        response += f"**Name:** {counsellor['name']}\n"
        response += f"**Branch:** {counsellor['branch']}\n"
        response += f"**Roll Range:** {counsellor['roll_range']}\n"
        
        if counsellor['email'] != 'Not available':
            response += f"**📧 Email:** {counsellor['email']}\n"
        if counsellor['phone'] != 'Not available':
            response += f"**📞 Phone:** {counsellor['phone']}\n"
        
        response += f"\n💡 Your counsellor can help you with academic guidance, course selection, and any student-related concerns."
        
        return response.strip()

# Global academic database instance
academic_db = AcademicDatabase()

# Helper functions for easy access
def get_faculty_by_subject_name(subject_name: str) -> str:
    """Get faculty teaching a subject - formatted for chatbot"""
    faculty_list = academic_db.get_faculty_by_subject(subject_name)
    return academic_db.format_faculty_response(faculty_list, subject_name)

def get_subjects_for_year_branch(year: int, branch: str) -> str:
    """Get subjects for year and branch - formatted for chatbot"""
    subjects = academic_db.get_subjects_by_year_and_branch(year, branch)
    return academic_db.format_subjects_response(subjects, year, branch)

def get_counsellor_for_roll(roll_number: str) -> str:
    """Get counsellor for a roll number - formatted for chatbot"""
    counsellor = academic_db.get_counsellor_by_roll(roll_number)
    return academic_db.format_counsellor_response(counsellor, roll_number)

def get_subjects_for_roll_number(roll_number: str) -> str:
    """Get subjects for a student based on their roll number"""
    year = academic_db.calculate_year_from_roll(roll_number)
    branch = academic_db.extract_branch_from_roll(roll_number)
    subjects = academic_db.get_subjects_by_year_and_branch(year, branch)
    return academic_db.format_subjects_response(subjects, year, branch)

# Test function
def test_academic_queries():
    """Test the academic database functions"""
    print("🧪 Testing Academic Database Functions...")
    
    # Test faculty query
    print("\n1. Testing faculty query for 'Machine Learning':")
    result = get_faculty_by_subject_name("Machine Learning")
    print(result)
    
    # Test subjects query
    print("\n2. Testing subjects query for 3rd year CS:")
    result = get_subjects_for_year_branch(3, "CS")
    print(result)
    
    # Test counsellor query
    print("\n3. Testing counsellor query for roll number '23CS045':")
    result = get_counsellor_for_roll("23CS045")
    print(result)
    
    # Test roll number based subjects
    print("\n4. Testing subjects for roll number '23CS045':")
    result = get_subjects_for_roll_number("23CS045")
    print(result)

if __name__ == "__main__":
    print("📚 Academic Database Module for CHARUSAT Chatbot")
    print("=" * 60)
    test_academic_queries()
