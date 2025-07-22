#!/usr/bin/env python3
"""
Academic Database Data Insertion Script
Populates the database with sample faculty, subjects, and counsellor data
"""

import sqlite3
from pathlib import Path
from academic_db import AcademicDatabase

def populate_academic_database():
    """Populate the database with sample data for testing"""
    
    academic_db = AcademicDatabase()
    db_path = academic_db.db_path
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🗃️ Populating Academic Database with sample data...")
        
        # Insert Faculty data
        faculty_data = [
            ('Dr. Rajesh Kumar', 'rajesh.kumar@charusat.edu.in', '+91-9876543210', 'Computer Science', 'Professor'),
            ('Dr. Priya Sharma', 'priya.sharma@charusat.edu.in', '+91-9876543211', 'Computer Science', 'Associate Professor'),
            ('Dr. Amit Patel', 'amit.patel@charusat.edu.in', '+91-9876543212', 'Computer Science', 'Assistant Professor'),
            ('Dr. Neha Gupta', 'neha.gupta@charusat.edu.in', '+91-9876543213', 'Computer Science', 'Professor'),
            ('Dr. Vikram Singh', 'vikram.singh@charusat.edu.in', '+91-9876543214', 'Computer Science', 'Associate Professor'),
            ('Dr. Kavya Joshi', 'kavya.joshi@charusat.edu.in', '+91-9876543215', 'Information Technology', 'Assistant Professor'),
            ('Dr. Ravi Mehta', 'ravi.mehta@charusat.edu.in', '+91-9876543216', 'Computer Science', 'Professor'),
            ('Dr. Sunita Agarwal', 'sunita.agarwal@charusat.edu.in', '+91-9876543217', 'Computer Science', 'Associate Professor'),
            ('Dr. Manoj Verma', 'manoj.verma@charusat.edu.in', '+91-9876543218', 'Information Technology', 'Assistant Professor'),
            ('Dr. Pooja Nair', 'pooja.nair@charusat.edu.in', '+91-9876543219', 'Computer Science', 'Professor')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO Faculty (name, email, phone, department, designation)
            VALUES (?, ?, ?, ?, ?)
        ''', faculty_data)
        
        print(f"✅ Inserted {len(faculty_data)} faculty records")
        
        # Insert Subject data for 3rd Year CS (Current academic year 2024-25)
        subjects_data = [
            # 3rd Year CS - Semester 5
            ('CS301', 'Machine Learning', 5, 3, 'CS', 'Introduction to ML algorithms and applications', 4),
            ('CS302', 'Database Management Systems', 5, 3, 'CS', 'Relational databases, SQL, and database design', 4),
            ('CS303', 'Computer Networks', 5, 3, 'CS', 'Network protocols, TCP/IP, and network security', 4),
            ('CS304', 'Software Engineering', 5, 3, 'CS', 'Software development lifecycle and methodologies', 3),
            ('CS305', 'Web Development', 5, 3, 'CS', 'Full-stack web development with modern frameworks', 3),
            ('CS306', 'Mobile Application Development', 5, 3, 'CS', 'Android and iOS app development', 3),
            
            # 3rd Year CS - Semester 6
            ('CS401', 'Artificial Intelligence', 6, 3, 'CS', 'AI concepts, search algorithms, and expert systems', 4),
            ('CS402', 'Data Structures and Algorithms Advanced', 6, 3, 'CS', 'Advanced data structures and algorithm analysis', 4),
            ('CS403', 'Operating Systems', 6, 3, 'CS', 'Process management, memory management, and file systems', 4),
            ('CS404', 'Compiler Design', 6, 3, 'CS', 'Lexical analysis, parsing, and code generation', 3),
            ('CS405', 'Information Security', 6, 3, 'CS', 'Cryptography, network security, and ethical hacking', 3),
            ('CS406', 'Human Computer Interaction', 6, 3, 'CS', 'User interface design and usability principles', 2),
            
            # 2nd Year CS - Semester 3
            ('CS201', 'Data Structures', 3, 2, 'CS', 'Arrays, linked lists, stacks, queues, trees', 4),
            ('CS202', 'Object Oriented Programming with Java', 3, 2, 'CS', 'OOP concepts using Java programming language', 4),
            ('CS203', 'Digital Logic Design', 3, 2, 'CS', 'Boolean algebra, logic gates, and digital circuits', 3),
            ('CS204', 'Discrete Mathematics', 3, 2, 'CS', 'Mathematical foundations for computer science', 3),
            ('CS205', 'Computer Organization', 3, 2, 'CS', 'CPU architecture, memory hierarchy, and I/O systems', 3),
            
            # 2nd Year CS - Semester 4
            ('CS251', 'Algorithms', 4, 2, 'CS', 'Algorithm design techniques and complexity analysis', 4),
            ('CS252', 'Database Systems', 4, 2, 'CS', 'Database concepts, ER modeling, and SQL', 4),
            ('CS253', 'Computer Graphics', 4, 2, 'CS', '2D and 3D graphics, rendering, and animation', 3),
            ('CS254', 'Theory of Computation', 4, 2, 'CS', 'Finite automata, formal languages, and computability', 3),
            ('CS255', 'Python Programming', 4, 2, 'CS', 'Python syntax, libraries, and application development', 3),
            
            # 1st Year CS - Semester 1
            ('CS101', 'Programming Fundamentals', 1, 1, 'CS', 'Basic programming concepts using C language', 4),
            ('CS102', 'Computer Fundamentals', 1, 1, 'CS', 'Introduction to computers and computing', 3),
            ('MA101', 'Engineering Mathematics-I', 1, 1, 'CS', 'Calculus, linear algebra, and differential equations', 4),
            ('PH101', 'Engineering Physics', 1, 1, 'CS', 'Mechanics, waves, and modern physics', 3),
            ('ENG101', 'English Communication', 1, 1, 'CS', 'Technical writing and communication skills', 2),
            
            # 1st Year CS - Semester 2
            ('CS151', 'Object Oriented Programming', 2, 1, 'CS', 'OOP concepts using C++ programming language', 4),
            ('CS152', 'Computer System Architecture', 2, 1, 'CS', 'Computer organization and assembly language', 3),
            ('MA151', 'Engineering Mathematics-II', 2, 1, 'CS', 'Vector calculus, Fourier series, and statistics', 4),
            ('CH101', 'Engineering Chemistry', 2, 1, 'CS', 'Chemical bonding, thermodynamics, and materials', 3),
            ('ENG151', 'Technical Communication', 2, 1, 'CS', 'Presentation skills and technical documentation', 2)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO Subject (code, name, semester, year, branch, description, credits)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', subjects_data)
        
        print(f"✅ Inserted {len(subjects_data)} subject records")
        
        # Insert Faculty-Subject mappings
        faculty_subject_mappings = [
            # Machine Learning
            (1, 1, '2024-25'),  # Dr. Rajesh Kumar - Machine Learning
            (4, 1, '2024-25'),  # Dr. Neha Gupta - Machine Learning
            
            # Database Management Systems
            (2, 2, '2024-25'),  # Dr. Priya Sharma - DBMS
            (7, 2, '2024-25'),  # Dr. Ravi Mehta - DBMS
            
            # Computer Networks
            (3, 3, '2024-25'),  # Dr. Amit Patel - Computer Networks
            (5, 3, '2024-25'),  # Dr. Vikram Singh - Computer Networks
            
            # Software Engineering
            (8, 4, '2024-25'),  # Dr. Sunita Agarwal - Software Engineering
            (2, 4, '2024-25'),  # Dr. Priya Sharma - Software Engineering
            
            # Web Development
            (6, 5, '2024-25'),  # Dr. Kavya Joshi - Web Development
            (9, 5, '2024-25'),  # Dr. Manoj Verma - Web Development
            
            # Mobile Application Development
            (9, 6, '2024-25'),  # Dr. Manoj Verma - Mobile App Dev
            (6, 6, '2024-25'),  # Dr. Kavya Joshi - Mobile App Dev
            
            # Artificial Intelligence
            (1, 7, '2024-25'),  # Dr. Rajesh Kumar - AI
            (10, 7, '2024-25'), # Dr. Pooja Nair - AI
            
            # Data Structures and Algorithms Advanced
            (4, 8, '2024-25'),  # Dr. Neha Gupta - Advanced DSA
            (7, 8, '2024-25'),  # Dr. Ravi Mehta - Advanced DSA
            
            # Operating Systems
            (3, 9, '2024-25'),  # Dr. Amit Patel - Operating Systems
            (5, 9, '2024-25'),  # Dr. Vikram Singh - Operating Systems
            
            # Compiler Design
            (10, 10, '2024-25'), # Dr. Pooja Nair - Compiler Design
            (1, 10, '2024-25'),  # Dr. Rajesh Kumar - Compiler Design
            
            # Information Security
            (5, 11, '2024-25'),  # Dr. Vikram Singh - Info Security
            (3, 11, '2024-25'),  # Dr. Amit Patel - Info Security
            
            # Human Computer Interaction
            (8, 12, '2024-25'),  # Dr. Sunita Agarwal - HCI
            (6, 12, '2024-25'),  # Dr. Kavya Joshi - HCI
            
            # 2nd Year subjects
            (2, 13, '2024-25'),  # Dr. Priya Sharma - Data Structures
            (4, 14, '2024-25'),  # Dr. Neha Gupta - Java OOP
            (7, 18, '2024-25'),  # Dr. Ravi Mehta - Algorithms
            (10, 21, '2024-25'), # Dr. Pooja Nair - Python Programming
            
            # 1st Year subjects
            (8, 22, '2024-25'),  # Dr. Sunita Agarwal - Programming Fundamentals
            (9, 27, '2024-25'),  # Dr. Manoj Verma - OOP with C++
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO FacultySubjectMap (faculty_id, subject_id, academic_year)
            VALUES (?, ?, ?)
        ''', faculty_subject_mappings)
        
        print(f"✅ Inserted {len(faculty_subject_mappings)} faculty-subject mappings")
        
        # Insert Counsellor data
        counsellors_data = [
            ('Dr. Rajesh Kumar', 'rajesh.kumar@charusat.edu.in', '+91-9876543210', 'CS', '23CS001', '23CS040', '2024-25'),
            ('Dr. Priya Sharma', 'priya.sharma@charusat.edu.in', '+91-9876543211', 'CS', '23CS041', '23CS080', '2024-25'),
            ('Dr. Amit Patel', 'amit.patel@charusat.edu.in', '+91-9876543212', 'CS', '23CS081', '23CS120', '2024-25'),
            ('Dr. Neha Gupta', 'neha.gupta@charusat.edu.in', '+91-9876543213', 'CS', '22CS001', '22CS040', '2024-25'),
            ('Dr. Vikram Singh', 'vikram.singh@charusat.edu.in', '+91-9876543214', 'CS', '22CS041', '22CS080', '2024-25'),
            ('Dr. Kavya Joshi', 'kavya.joshi@charusat.edu.in', '+91-9876543215', 'IT', '23IT001', '23IT040', '2024-25'),
            ('Dr. Ravi Mehta', 'ravi.mehta@charusat.edu.in', '+91-9876543216', 'CS', '21CS001', '21CS040', '2024-25'),
            ('Dr. Sunita Agarwal', 'sunita.agarwal@charusat.edu.in', '+91-9876543217', 'CS', '24CS001', '24CS040', '2024-25'),
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO Counsellor (name, email, phone, branch, roll_range_start, roll_range_end, academic_year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', counsellors_data)
        
        print(f"✅ Inserted {len(counsellors_data)} counsellor records")
        
        conn.commit()
        print("\n🎉 Academic database populated successfully!")
        
        # Print summary
        cursor.execute("SELECT COUNT(*) FROM Faculty")
        faculty_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Subject")
        subject_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM FacultySubjectMap")
        mapping_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Counsellor")
        counsellor_count = cursor.fetchone()[0]
        
        print(f"\n📊 Database Summary:")
        print(f"   Faculty: {faculty_count}")
        print(f"   Subjects: {subject_count}")
        print(f"   Faculty-Subject Mappings: {mapping_count}")
        print(f"   Counsellors: {counsellor_count}")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        conn.rollback()
    finally:
        conn.close()

def test_queries():
    """Test some common queries"""
    print("\n🧪 Testing Common Academic Queries...")
    print("=" * 60)
    
    from academic_db import get_faculty_by_subject_name, get_subjects_for_year_branch, get_counsellor_for_roll, get_subjects_for_roll_number
    
    # Test 1: Who teaches Machine Learning?
    print("1️⃣ Query: Who teaches Machine Learning?")
    result = get_faculty_by_subject_name("Machine Learning")
    print(result)
    print()
    
    # Test 2: Who teaches ML (abbreviation)?
    print("2️⃣ Query: Who teaches ML?")
    result = get_faculty_by_subject_name("ML")
    print(result)
    print()
    
    # Test 3: 3rd year CS subjects
    print("3️⃣ Query: Give me 3rd year CSE subjects")
    result = get_subjects_for_year_branch(3, "CS")
    print(result)
    print()
    
    # Test 4: Counsellor for specific roll number
    print("4️⃣ Query: Who's my student counsellor for roll number 23CS045?")
    result = get_counsellor_for_roll("23CS045")
    print(result)
    print()
    
    # Test 5: Subjects for roll number
    print("5️⃣ Query: What subjects does 23CS045 have?")
    result = get_subjects_for_roll_number("23CS045")
    print(result)
    print()

if __name__ == "__main__":
    print("🗃️ Academic Database Population Script")
    print("=" * 60)
    
    # Populate the database
    populate_academic_database()
    
    # Test the queries
    test_queries()
