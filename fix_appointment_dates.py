#!/usr/bin/env python3
"""
Appointment Date Fixer - Fixes appointment date issues in the database
Compatible with Python 3.13
"""
import os
import sqlite3
from datetime import datetime, timedelta
import re
import sys

# The correct database path
DB_PATH = '/Volumes/Rabah_SSD/enrpreneurship/health/health/instance/health_app.db'

def fix_appointment_dates():
    """Fix appointment dates based on hints in notes field"""
    print(f"---- Fixing Appointment Dates in {DB_PATH} ----")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, inspect all appointment date types
        cursor.execute("SELECT id, appointment_date, typeof(appointment_date) FROM appointments")
        all_appointments = cursor.fetchall()
        print("\nAppointment date types:")
        for appt in all_appointments:
            print(f"ID: {appt['id']} - Date: {appt['appointment_date']} - Type: {appt['typeof(appointment_date)']}")

        # Then query for problematic appointments
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE appointment_date = '2025' 
               OR appointment_date = 2025
               OR typeof(appointment_date) = 'integer'
               OR typeof(appointment_date) = 'text' AND NOT date(appointment_date) IS date(appointment_date)
        """)
        appointments = cursor.fetchall()
        
        print(f"Found {len(appointments)} appointments with date issues")
        
        # Prepare for batch update
        updates = []
        date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')  # More general date pattern
        
        for appt in appointments:
            appt_id = appt['id']
            appt_date = appt['appointment_date']
            notes = appt['notes'] or ""
            
            # Try to extract date from notes
            date_match = date_pattern.search(notes)
            if date_match:
                extracted_date = date_match.group(1)
                updates.append((extracted_date, appt_id))
                print(f"Appointment #{appt_id}: Will update from '{appt_date}' to '{extracted_date}'")
            else:
                # Fallback to created_at date if no hint in notes
                try:
                    created_date = datetime.fromisoformat(appt['created_at']).date()
                    # Use timedelta for safe date calculation
                    appointment_date = created_date + timedelta(days=14)
                    updates.append((appointment_date.isoformat(), appt_id))
                    print(f"Appointment #{appt_id}: No date in notes, using estimate: '{appointment_date}'")
                except (ValueError, TypeError, OverflowError) as e:
                    print(f"Appointment #{appt_id}: Error processing date: {e}")
        
        # Confirm with user
        if updates:
            print(f"\nReady to update {len(updates)} appointment dates")
            choice = input("Proceed with updates? (y/n): ")
            
            if choice.lower() == 'y':
                # Execute updates
                cursor.executemany(
                    "UPDATE appointments SET appointment_date = ? WHERE id = ?",
                    updates
                )
                conn.commit()
                print(f"Successfully updated {len(updates)} appointment dates")
            else:
                print("Update cancelled")
        else:
            print("No appointments to update")
        
        conn.close()
        return True
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = fix_appointment_dates()
    if success:
        print("\nAppointment date fixing completed.")
    else:
        print("\nAppointment date fixing failed.")
        sys.exit(1)
