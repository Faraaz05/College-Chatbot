#!/usr/bin/env python3
"""
CHARUSAT Attendance API
A simple function that takes student ID and password and returns cleaned attendance data.
"""

import requests
from bs4 import BeautifulSoup
import urllib3
import json
import re
from typing import Dict, List, Optional, Tuple

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_student_attendance(student_id: str, password: str) -> Dict:
    """
    Get cleaned attendance data for a student.
    
    Args:
        student_id (str): Student ID (e.g., "23CS012")
        password (str): Student password
        
    Returns:
        Dict: Dictionary containing:
            - success (bool): Whether the operation was successful
            - data (List): List of attendance records if successful
            - message (str): Status message
            - summary (Dict): Summary statistics if successful
    """
    
    # Validate inputs
    if not student_id or not password:
        raise ValueError("Student ID and password must be provided")
    
    if not isinstance(student_id, str) or not isinstance(password, str):
        raise ValueError("Student ID and password must be strings")
    
    try:
        # Step 1: Create session and login
        session = create_session()
        dashboard_html = login_to_portal(session, student_id, password)
        
        if not dashboard_html:
            return {
                "success": False,
                "data": [],
                "message": f"Failed to login for student {student_id}. Please check your credentials.",
                "summary": {}
            }
        
        # Step 2: Check for gross attendance on dashboard first
        dashboard_soup = BeautifulSoup(dashboard_html, "html.parser")
        gross_attendance_element = dashboard_soup.find(id="lblPopGrossAtt")
        
        if gross_attendance_element:
            gross_text = gross_attendance_element.get_text().strip()
            
            # Extract gross attendance
            gross_attendance = None
            gross_match = re.search(r'(\d+(?:\.\d+)?)\s*%', gross_text)
            if not gross_match:
                gross_match = re.search(r'(\d+(?:\.\d+)?)', gross_text)
            
            if gross_match:
                gross_attendance = float(gross_match.group(1))
                
                # Return concise response with gross attendance
                return {
                    "success": True,
                    "message": f"Attendance for student {student_id} retrieved: Overall {gross_attendance}%",
                    "data": [],
                    "summary": {
                        "gross_attendance": gross_attendance, 
                        "overall_percentage": gross_attendance,
                        "student_id": student_id
                    }
                }
        
        # Step 3: Get detailed attendance data if needed
        attendance_html = get_attendance_page(session, dashboard_html)
        
        if not attendance_html:
            return {
                "success": False,
                "data": [],
                "message": f"Failed to access detailed attendance page for student {student_id}",
                "summary": {}
            }
        
        # Step 4: Extract and clean data
        raw_data, gross_attendance_from_detail = extract_attendance_tables(attendance_html)
        cleaned_data = clean_attendance_data(raw_data)
        
        # Use gross attendance from dashboard if available, otherwise from detail page
        final_gross_attendance = gross_attendance if 'gross_attendance' in locals() else gross_attendance_from_detail
        
        if not cleaned_data and final_gross_attendance is None:
            return {
                "success": False,
                "data": [],
                "message": f"No attendance data found for student {student_id}",
                "summary": {}
            }
        
        # Step 5: Generate summary
        summary = generate_summary(cleaned_data, final_gross_attendance)
        summary["student_id"] = student_id
        
        return {
            "success": True,
            "data": cleaned_data,
            "message": f"Attendance for student {student_id} retrieved: Overall {summary.get('overall_percentage', 0)}% ({len(cleaned_data)} records)",
            "summary": summary
        }
        
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"Error retrieving attendance for student {student_id}: {str(e)}",
            "summary": {}
        }


def create_session() -> requests.Session:
    """Create a session with proper headers"""
    session = requests.Session()
    session.verify = False
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    
    return session


def login_to_portal(session: requests.Session, student_id: str, password: str) -> Optional[str]:
    """Login to the CHARUSAT portal and return dashboard HTML"""
    
    # Get login page
    print("📄 Accessing login page...")
    login_response = session.get("https://charusat.edu.in:912/eGovernance/")
    
    if login_response.status_code != 200:
        print(f"❌ Failed to get login page: {login_response.status_code}")
        return None
    
    # Parse login form
    soup = BeautifulSoup(login_response.text, "html.parser")
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})
    viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
    event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})
    
    # Login
    print("🔐 Logging in...")
    login_payload = {
        "txtUserName": student_id,
        "txtPassword": password,
        "__VIEWSTATE": viewstate['value'] if viewstate else "",
        "__VIEWSTATEGENERATOR": viewstate_gen['value'] if viewstate_gen else "",
        "__EVENTVALIDATION": event_validation['value'] if event_validation else "",
        "__EVENTTARGET": "btnLogin",
        "__EVENTARGUMENT": "",
    }
    
    login_result = session.post("https://charusat.edu.in:912/eGovernance/", data=login_payload)
    
    if login_result.status_code != 200:
        print(f"❌ Login failed: {login_result.status_code}")
        return None
    
    # Check if we need to navigate to e-governance
    login_soup = BeautifulSoup(login_result.text, "html.parser")
    dashboard_div = login_soup.find("div", {"id": "pnlGrossAtt"})
    
    if dashboard_div:
        print("✅ Already on dashboard")
        return login_result.text
    else:
        # Navigate to e-governance
        print("🎯 Navigating to e-Governance...")
        egovernance_link = login_soup.find("a", href=lambda x: x and "dlAppList" in x)
        
        if not egovernance_link:
            print("❌ No e-governance link found")
            return None
        
        # Get fresh form data
        viewstate = login_soup.find("input", {"name": "__VIEWSTATE"})
        viewstate_gen = login_soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        event_validation = login_soup.find("input", {"name": "__EVENTVALIDATION"})
        
        egovernance_payload = {
            "__VIEWSTATE": viewstate['value'] if viewstate else "",
            "__VIEWSTATEGENERATOR": viewstate_gen['value'] if viewstate_gen else "",
            "__EVENTVALIDATION": event_validation['value'] if event_validation else "",
            "__EVENTTARGET": "dlAppList$ctl00$ImageButton1",
            "__EVENTARGUMENT": "",
        }
        
        dashboard_response = session.post(login_result.url, data=egovernance_payload)
        
        if dashboard_response.status_code == 200:
            print("✅ Dashboard loaded")
            return dashboard_response.text
        else:
            print(f"❌ Failed to load dashboard: {dashboard_response.status_code}")
            return None


def get_attendance_page(session: requests.Session, dashboard_html: str) -> Optional[str]:
    """Click on attendance section to get attendance data"""
    
    print("🎯 Getting detailed attendance data...")
    
    # Parse dashboard and get form data
    soup = BeautifulSoup(dashboard_html, "html.parser")
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})
    viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
    event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})
    
    # Make postback request to get attendance data
    postback_payload = {
        "__VIEWSTATE": viewstate['value'] if viewstate else "",
        "__VIEWSTATEGENERATOR": viewstate_gen['value'] if viewstate_gen else "",
        "__EVENTVALIDATION": event_validation['value'] if event_validation else "",
        "__EVENTTARGET": "grdGrossAtt$ctl01$lnkRequestViewTT",
        "__EVENTARGUMENT": "",
    }
    
    print("📡 Making postback request...")
    response = session.post("https://charusat.edu.in:912/eGovernance/frmAppSelection.aspx", 
                           data=postback_payload, timeout=30)
    
    if response.status_code == 200:
        print("✅ Detailed attendance data retrieved")
        return response.text
    else:
        print(f"❌ Failed to get detailed attendance data: {response.status_code}")
        return None


def extract_attendance_tables(html_content: str) -> Tuple[List[Dict], Optional[str]]:
    """Extract attendance data from HTML tables and gross attendance"""
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract gross attendance from lblPopGrossAtt
    gross_attendance_element = soup.find(id="lblPopGrossAtt")
    gross_attendance = None
    if gross_attendance_element:
        gross_text = gross_attendance_element.get_text().strip()
        print(f"🔍 Raw gross attendance text: '{gross_text}'")
        
        # Try different patterns to extract percentage
        # Pattern 1: Look for percentage with % sign
        gross_match = re.search(r'(\d+(?:\.\d+)?)\s*%', gross_text)
        if not gross_match:
            # Pattern 2: Look for standalone number (might be without %)
            gross_match = re.search(r'(\d+(?:\.\d+)?)', gross_text)
        
        if gross_match:
            gross_attendance = float(gross_match.group(1))
            print(f"📊 Gross Attendance: {gross_attendance}%")
        else:
            print(f"⚠️ Could not parse gross attendance from: '{gross_text}'")
    
    # Extract detailed attendance tables
    tables = soup.find_all("table")
    attendance_data = []
    
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        
        # Check if this looks like an attendance table
        header_row = rows[0]
        header_text = ' '.join([th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])])
        
        if any(word in header_text for word in ['course', 'subject', 'attendance', 'present', 'percentage']):
            # Get headers
            headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
            
            # Extract data rows
            for row in rows[1:]:
                cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                if cells and any(cell for cell in cells):
                    row_data = dict(zip(headers, cells))
                    attendance_data.append(row_data)
    
    return attendance_data, gross_attendance


def clean_attendance_data(raw_data: List[Dict]) -> List[Dict]:
    """Clean and format the attendance data"""
    
    cleaned_data = []
    course_names = {}
    
    # First pass: collect course names
    for record in raw_data:
        if 'Course Code' in record and 'Course Name' in record:
            code = record['Course Code'].strip()
            name = record['Course Name'].strip()
            course_names[code] = name
    
    # Second pass: clean attendance records
    for record in raw_data:
        if all(key in record for key in ['Course', 'Class Type', 'Percentage']):
            
            # Clean the data
            course = record['Course'].strip()
            class_type = record['Class Type'].strip()
            percentage = record['Percentage'].strip()
            
            # Clean the Present/Total field
            present_total = record.get('Present / Total', record.get('Present/Total', '')).strip()
            present_total = re.sub(r'\s+', ' ', present_total)
            present_total = present_total.replace('/\n', '/').replace('\n/', '/')
            
            # Extract present and total numbers
            present_match = re.search(r'(\d+)\s*/\s*(\d+)', present_total)
            if present_match:
                present = int(present_match.group(1))
                total = int(present_match.group(2))
            else:
                present = None
                total = None
            
            # Extract percentage number
            percentage_match = re.search(r'(\d+(?:\.\d+)?)%', percentage)
            percentage_num = float(percentage_match.group(1)) if percentage_match else None
            
            cleaned_record = {
                'course_code': course,
                'class_type': class_type,
                'present': present,
                'total': total,
                'percentage': percentage_num,
                'raw_present_total': present_total,
                'raw_percentage': percentage
            }
            
            # Add course name if available
            if course in course_names:
                cleaned_record['course_name'] = course_names[course]
            
            cleaned_data.append(cleaned_record)
    
    return cleaned_data


def generate_summary(cleaned_data: List[Dict], gross_attendance: Optional[float] = None) -> Dict:
    """Generate summary statistics"""
    
    summary = {}
    
    # Add gross attendance if available
    if gross_attendance is not None:
        summary['gross_attendance'] = gross_attendance
        print(f"🎯 Using gross attendance: {gross_attendance}%")
    
    if not cleaned_data:
        return summary
    
    total_present = sum(record['present'] or 0 for record in cleaned_data)
    total_classes = sum(record['total'] or 0 for record in cleaned_data)
    calculated_percentage = (total_present / total_classes * 100) if total_classes > 0 else 0
    
    # Group by subject, keeping lecture and lab separate, avoiding duplicates
    subjects = {}
    seen_combinations = set()
    
    for record in cleaned_data:
        course = record['course_code']
        class_type = record['class_type']
        present = record['present'] or 0
        total = record['total'] or 0
        
        # Create unique identifier for this specific record
        record_id = f"{course}_{class_type}_{present}_{total}"
        
        # Skip if we've already seen this exact record
        if record_id in seen_combinations:
            continue
        seen_combinations.add(record_id)
        
        # Create unique key for each subject-classtype combination
        subject_key = f"{course}_{class_type}"
        display_name = f"{record.get('course_name', course)} ({class_type})"
        
        # Use only the first occurrence of each subject-type combination
        if subject_key not in subjects:
            subjects[subject_key] = {
                'course_name': display_name,
                'course_code': course,
                'class_type': class_type,
                'total_present': present,
                'total_classes': total,
                'classes': [record]
            }
    
    # Calculate subject percentages for each lecture/lab separately
    for subject in subjects.values():
        if subject['total_classes'] > 0:
            subject['percentage'] = subject['total_present'] / subject['total_classes'] * 100
        else:
            subject['percentage'] = 0
    
    # Update summary with detailed data
    summary.update({
        'total_present': total_present,
        'total_classes': total_classes,
        'calculated_percentage': round(calculated_percentage, 2),
        'total_records': len(cleaned_data),
        'subjects': subjects
    })
    
    # Use gross attendance as overall if available, otherwise use calculated
    if gross_attendance is not None:
        summary['overall_percentage'] = gross_attendance
    else:
        summary['overall_percentage'] = summary['calculated_percentage']
    
    return summary


def save_attendance_data(data: List[Dict], filename: str = "attendance_data.json") -> bool:
    """Save attendance data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving data: {e}")
        return False


def print_attendance_summary(result: Dict) -> None:
    """Print a formatted summary of attendance data"""
    
    if not result['success']:
        print(f"❌ {result['message']}")
        return
    
    data = result['data']
    summary = result['summary']
    
    print(f"\n📊 Attendance Summary")
    print("=" * 60)
    
    for record in data:
        course = record['course_code']
        class_type = record['class_type']
        present = record['present'] or 0
        total = record['total'] or 0
        percentage = record['percentage'] or 0
        
        print(f"{course:<15} {class_type:<5} | {present:2d}/{total:2d} ({percentage:5.1f}%)")
    
    print("=" * 60)
    print(f"{'OVERALL':<21} | {summary['total_present']:2d}/{summary['total_classes']:2d} ({summary['overall_percentage']:5.1f}%)")
    
    # Show both gross and calculated if different
    if 'gross_attendance' in summary and 'calculated_percentage' in summary:
        if abs(summary['gross_attendance'] - summary['calculated_percentage']) > 0.1:
            print(f"{'GROSS (Official)':<21} | {summary['gross_attendance']:5.1f}%")
            print(f"{'CALCULATED':<21} | {summary['calculated_percentage']:5.1f}%")
    
    print(f"Total Records: {summary['total_records']}")


# Example usage and CLI interface
def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Get CHARUSAT student attendance data")
    parser.add_argument("student_id", help="Student ID (e.g., 23CS012)")
    parser.add_argument("password", help="Student password")
    parser.add_argument("--save", "-s", help="Save data to JSON file", metavar="FILENAME")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
    
    args = parser.parse_args()
    
    # Get attendance data
    result = get_student_attendance(args.student_id, args.password)
    
    if not args.quiet:
        print_attendance_summary(result)
    
    # Save data if requested
    if args.save and result['success']:
        if save_attendance_data(result['data'], args.save):
            print(f"💾 Data saved to {args.save}")
    
    return result


if __name__ == "__main__":
    # Example usage:
    # python get_attendance.py 23CS012 011105
    # python get_attendance.py 23CS012 011105 --save my_attendance.json
    
    result = main()
