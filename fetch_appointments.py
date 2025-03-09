import sys
import os

# Add the directory to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from health import create_app, db

app = create_app()

with app.app_context():
    result = db.session.execute('SELECT appointment_date FROM appointments')
    for row in result:
        print(row[0])  # Print each appointment date
