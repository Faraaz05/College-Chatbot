#!/usr/bin/env python3
"""
Simple Attendance Scraper - Direct HTML approach
Just login, get to dashboard, click on pnlGrossAtt div, scrape the table
"""

import requests
from bs4 import BeautifulSoup
import urllib3
import time
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_session():
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

def login_and_get_dashboard(session):
    """Login and get to the dashboard"""
    print("🎓 Starting simple attendance scraper...")
    print("=" * 50)
    
    # Step 1: Get login page
    print("📄 Getting login page...")
    login_response = session.get("https://charusat.edu.in:912/eGovernance/")
    
    if login_response.status_code != 200:
        print(f"❌ Failed to get login page: {login_response.status_code}")
        return None
    
    print(f"✅ Login page loaded ({len(login_response.text)} characters)")
    
    # Parse login form
    soup = BeautifulSoup(login_response.text, "html.parser")
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})
    viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
    event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})
    
    # Step 2: Login
    print("🔐 Logging in...")
    credentials = {
        "username": "23CS007",
        "password": "siraj@4103"
    }
    
    login_payload = {
        "txtUserName": credentials["username"],
        "txtPassword": credentials["password"],
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
    
    print(f"✅ Login successful ({len(login_result.text)} characters)")
    
    # Step 3: Navigate to e-Governance dashboard
    print("🎯 Navigating to e-Governance dashboard...")
    
    login_soup = BeautifulSoup(login_result.text, "html.parser")
    
    # Check if we're already on dashboard or need to navigate to e-governance
    dashboard_div = login_soup.find("div", {"id": "pnlGrossAtt"})
    
    if dashboard_div:
        print("✅ Already on dashboard with pnlGrossAtt div!")
        return login_result.text
    else:
        # Need to navigate to e-governance application
        print("🔍 Looking for e-governance link...")
        
        egovernance_link = login_soup.find("a", href=lambda x: x and "dlAppList" in x)
        
        if egovernance_link:
            print("✅ Found e-governance link, navigating...")
            
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
                print(f"✅ Dashboard loaded ({len(dashboard_response.text)} characters)")
                
                # Save dashboard for inspection
                with open("dashboard.html", "w", encoding="utf-8") as f:
                    f.write(dashboard_response.text)
                print("💾 Dashboard saved to 'dashboard.html'")
                
                return dashboard_response.text
            else:
                print(f"❌ Failed to load dashboard: {dashboard_response.status_code}")
                return None
        else:
            print("❌ No e-governance link found")
            return None

def click_attendance_section(session, dashboard_html):
    """Click on the pnlGrossAtt div to get attendance data"""
    print("\n🎯 Looking for attendance section (pnlGrossAtt)...")
    
    soup = BeautifulSoup(dashboard_html, "html.parser")
    
    # Find the pnlGrossAtt div
    attendance_div = soup.find("div", {"id": "pnlGrossAtt"})
    
    if not attendance_div:
        print("❌ pnlGrossAtt div not found in dashboard")
        print("🔍 Let's see what divs are available...")
        
        # Look for any divs with 'att' in their ID
        all_divs = soup.find_all("div", id=True)
        att_divs = [div for div in all_divs if 'att' in div.get('id', '').lower()]
        
        if att_divs:
            print("📋 Found divs with 'att' in ID:")
            for div in att_divs:
                print(f"   - {div.get('id')}")
        else:
            print("📋 No divs with 'att' found. All div IDs:")
            for div in all_divs[:20]:  # Show first 20
                div_id = div.get('id', 'no-id')
                print(f"   - {div_id}")
        
        return None
    
    print("✅ Found pnlGrossAtt div!")
    
    # Look for clickable elements within this div
    clickable_elements = attendance_div.find_all(['a', 'button', 'input'], href=True) + \
                        attendance_div.find_all(['a', 'button', 'input'], onclick=True)
    
    if not clickable_elements:
        # Maybe the div itself is clickable, look for any links or buttons in the attendance area
        print("🔍 Looking for clickable elements near attendance section...")
        
        # Look for elements with attendance-related text or IDs
        potential_clicks = soup.find_all(['a', 'button', 'input'], 
                                       attrs={'onclick': lambda x: x and ('attendance' in x.lower() or 'gross' in x.lower())})
        
        if not potential_clicks:
            # Look for image buttons or links that might trigger attendance display
            potential_clicks = soup.find_all('input', {'type': 'image'})
            potential_clicks += soup.find_all('a', href=lambda x: x and 'javascript:__doPostBack' in x)
        
        clickable_elements = potential_clicks
    
    if clickable_elements:
        print(f"📋 Found {len(clickable_elements)} clickable elements in attendance section:")
        
        for i, element in enumerate(clickable_elements):
            element_type = element.name
            element_id = element.get('id', 'no-id')
            onclick = element.get('onclick', '')
            href = element.get('href', '')
            
            print(f"   {i+1}. {element_type} - ID: {element_id}")
            if onclick:
                print(f"      onclick: {onclick[:100]}...")
            if href:
                print(f"      href: {href}")
        
        # Try clicking the first relevant element
        first_element = clickable_elements[0]
        print(f"\n🖱️  Trying to click: {first_element.get('id', 'unnamed')} ({first_element.name})")
        
        # Handle different types of clicks
        onclick = first_element.get('onclick', '')
        href = first_element.get('href', '')
        
        if onclick and '__doPostBack' in onclick:
            return handle_postback_click(session, dashboard_html, onclick)
        elif href and href.startswith('javascript:'):
            return handle_javascript_click(session, dashboard_html, href)
        else:
            print("❓ Unknown click type, trying as postback...")
            return handle_postback_click(session, dashboard_html, onclick)
    
    else:
        print("❌ No clickable elements found in attendance section")
        return None

def handle_postback_click(session, current_html, onclick):
    """Handle ASP.NET postback click"""
    print("📝 Handling ASP.NET postback...")
    
    import re
    
    # Extract __doPostBack parameters
    if '__doPostBack' in onclick:
        match = re.search(r"__doPostBack\('([^']*)',\s*'([^']*)'\)", onclick)
        if match:
            event_target = match.group(1)
            event_argument = match.group(2)
            print(f"   Event Target: {event_target}")
            print(f"   Event Argument: {event_argument}")
        else:
            print("❌ Could not parse __doPostBack parameters")
            return None
    else:
        # Try to find a reasonable default
        print("❓ No __doPostBack found, trying default attendance target...")
        event_target = "grdGrossAtt$ctl01$lnkRequestViewTT"  # Based on your sample
        event_argument = ""
    
    # Parse current page for form data
    soup = BeautifulSoup(current_html, "html.parser")
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})
    viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
    event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})
    
    # Create postback payload
    postback_payload = {
        "__VIEWSTATE": viewstate['value'] if viewstate else "",
        "__VIEWSTATEGENERATOR": viewstate_gen['value'] if viewstate_gen else "",
        "__EVENTVALIDATION": event_validation['value'] if event_validation else "",
        "__EVENTTARGET": event_target,
        "__EVENTARGUMENT": event_argument,
    }
    
    print("🚀 Making postback request...")
    
    # Make the postback request
    response = session.post("https://charusat.edu.in:912/eGovernance/frmAppSelection.aspx", 
                           data=postback_payload)
    
    if response.status_code == 200:
        print(f"✅ Postback successful ({len(response.text)} characters)")
        
        # Save the response
        with open("attendance_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("💾 Attendance page saved to 'attendance_page.html'")
        
        return response.text
    else:
        print(f"❌ Postback failed: {response.status_code}")
        return None

def handle_javascript_click(session, current_html, href):
    """Handle JavaScript click"""
    print(f"🔧 Handling JavaScript: {href[:100]}...")
    
    # For now, treat JavaScript links as postbacks
    # This is a simplification - in reality we'd need to execute the JavaScript
    return handle_postback_click(session, current_html, href)

def extract_attendance_table(html_content):
    """Extract attendance data from HTML"""
    print("\n📊 Extracting attendance table...")
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Look for tables with attendance data
    tables = soup.find_all("table")
    attendance_data = []
    
    for i, table in enumerate(tables):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        
        # Check if this looks like an attendance table
        header_row = rows[0]
        header_text = ' '.join([th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])])
        
        if any(word in header_text for word in ['course', 'subject', 'attendance', 'present', 'percentage']):
            print(f"📋 Found attendance table {i+1}:")
            print(f"   Headers: {header_text}")
            
            # Get headers
            headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
            
            # Extract data rows
            for j, row in enumerate(rows[1:], 1):
                cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                if cells and any(cell for cell in cells):
                    row_data = dict(zip(headers, cells))
                    attendance_data.append(row_data)
                    print(f"   Row {j}: {' | '.join(cells)}")
    
    # Save attendance data
    if attendance_data:
        with open("extracted_attendance_data.json", "w", encoding="utf-8") as f:
            json.dump(attendance_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Extracted {len(attendance_data)} attendance records")
        print("💾 Data saved to 'extracted_attendance_data.json'")
    else:
        print("❌ No attendance tables found")
    
    return attendance_data

def main():
    """Main function"""
    session = create_session()
    
    # Step 1: Login and get dashboard
    dashboard_html = login_and_get_dashboard(session)
    
    if not dashboard_html:
        print("❌ Could not get dashboard")
        return
    
    # Step 2: Click on attendance section
    attendance_html = click_attendance_section(session, dashboard_html)
    
    if not attendance_html:
        print("❌ Could not get attendance data")
        return
    
    # Step 3: Extract attendance table
    attendance_data = extract_attendance_table(attendance_html)
    
    if attendance_data:
        print(f"\n🎉 Successfully extracted {len(attendance_data)} attendance records!")
        print("\n📈 Summary:")
        for record in attendance_data:
            subject = record.get('Course', record.get('Subject', 'Unknown'))
            percentage = record.get('Percentage', record.get('Attendance', 'N/A'))
            print(f"   {subject}: {percentage}")
    else:
        print("❌ No attendance data extracted")

if __name__ == "__main__":
    main()
