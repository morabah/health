#!/usr/bin/env python3
"""
Appointment Date Inspector and Fixer - Examines and fixes appointment date issues
Compatible with Python 3.13
"""
import os
import sqlite3
from datetime import datetime, date
import sys

# The correct database path we found
DB_PATH = '/Volumes/Rabah_SSD/enrpreneurship/health/health/instance/health_app.db'

def inspect_and_fix_appointments():
    """Inspect appointment dates and offer to fix any issues"""
    print(f"---- Inspecting Appointments in {DB_PATH} ----")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get appointment table structure
        cursor.execute("PRAGMA table_info(appointments)")
        columns = cursor.fetchall()
        print("Appointment table structure:")
        for col in columns:
            print(f"  {col['name']} ({col['type']})")
        
        # Query all appointments
        cursor.execute("""
            SELECT a.*, 
                   p.first_name as patient_first_name, p.last_name as patient_last_name,
                   d.first_name as doctor_first_name, d.last_name as doctor_last_name
            FROM appointments a
            JOIN users p ON a.patient_id = p.id
            JOIN users d ON a.doctor_id = d.id
            ORDER BY a.id
        """)
        appointments = cursor.fetchall()
        
        print(f"\nFound {len(appointments)} appointments")
        
        # Check for date format issues
        date_issues = []
        for appt in appointments:
            appt_date = appt['appointment_date']
            if appt_date == '2025' or not isinstance(appt_date, (date, str)) or len(str(appt_date)) < 8:
                date_issues.append(appt)
        
        if date_issues:
            print(f"\nFound {len(date_issues)} appointments with potential date issues:")
            for i, appt in enumerate(date_issues[:10]):  # Show first 10 for brevity
                print(f"\n{i+1}. Appointment #{appt['id']}:")
                print(f"   Date: '{appt['appointment_date']}' (Type: {type(appt['appointment_date']).__name__})")
                print(f"   Time: {appt['start_time']} - {appt['end_time']}")
                print(f"   Patient: {appt['patient_first_name']} {appt['patient_last_name']}")
                print(f"   Doctor: {appt['doctor_first_name']} {appt['doctor_last_name']}")
                print(f"   Status: {appt['status']}")
                print(f"   Created: {appt['created_at']}")
                print(f"   Updated: {appt['updated_at']}")
            
            if len(date_issues) > 10:
                print(f"\n... and {len(date_issues) - 10} more appointments with issues")
                
            # Look for date hints in notes or other fields
            print("\nAnalyzing for date hints...")
            for appt in date_issues[:5]:
                notes = appt['notes'] or ""
                if "completed on" in notes.lower():
                    date_hint = notes.split("completed on")[1].strip()
                    print(f"Appointment #{appt['id']} has hint in notes: '{date_hint}'")
                
                # Check created_at field for hints
                created = appt['created_at']
                if created:
                    try:
                        created_date = datetime.fromisoformat(created).date()
                        print(f"Appointment #{appt['id']} created on {created_date}")
                    except (ValueError, TypeError):
                        pass
        else:
            print("No date format issues found in appointments.")
        
        conn.close()
        return True
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = inspect_and_fix_appointments()
    if success:
        print("\nAppointment inspection completed.")
    else:
        print("\nAppointment inspection failed.")
        sys.exit(1)