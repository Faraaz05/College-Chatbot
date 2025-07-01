#!/usr/bin/env python3
"""
Clean and format the extracted attendance data
"""

import json
import re

def clean_attendance_data():
    """Clean and format the attendance data"""
    
    with open('extracted_attendance_data.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print("🧹 Cleaning attendance data...")
    
    cleaned_data = []
    
    for record in raw_data:
        # Look for records with Course, Class Type, and Percentage
        if all(key in record for key in ['Course', 'Class Type', 'Percentage']):
            
            # Clean the course name
            course = record['Course'].strip()
            class_type = record['Class Type'].strip()
            percentage = record['Percentage'].strip()
            
            # Clean the Present/Total field
            present_total = record.get('Present / Total', record.get('Present/Total', '')).strip()
            present_total = re.sub(r'\s+', ' ', present_total)  # Remove extra whitespace
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
            
            cleaned_data.append(cleaned_record)
    
    # Also add course name mappings from the data
    course_names = {}
    for record in raw_data:
        if 'Course Code' in record and 'Course Name' in record:
            code = record['Course Code'].strip()
            name = record['Course Name'].strip()
            course_names[code] = name
    
    # Add course names to cleaned data
    for record in cleaned_data:
        course_code = record['course_code']
        if course_code in course_names:
            record['course_name'] = course_names[course_code]
    
    # Save cleaned data
    with open('attendance_data_clean.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cleaned {len(cleaned_data)} attendance records")
    print("💾 Clean data saved to 'attendance_data_clean.json'")
    
    # Display summary
    print("\n📊 Attendance Summary:")
    print("=" * 60)
    
    total_present = 0
    total_classes = 0
    
    for record in cleaned_data:
        course = record['course_code']
        class_type = record['class_type']
        present = record['present'] or 0
        total = record['total'] or 0
        percentage = record['percentage'] or 0
        
        total_present += present
        total_classes += total
        
        print(f"{course:<15} {class_type:<5} | {present:2d}/{total:2d} ({percentage:5.1f}%)")
    
    overall_percentage = (total_present / total_classes * 100) if total_classes > 0 else 0
    print("=" * 60)
    print(f"{'OVERALL':<21} | {total_present:2d}/{total_classes:2d} ({overall_percentage:5.1f}%)")
    
    return cleaned_data

if __name__ == "__main__":
    clean_attendance_data()
