import sys
import os
from sqlalchemy import create_engine

# Add the directory to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from health import create_app
from health.models import db

app = create_app()

with app.app_context():
    # Directly query the database
    result = db.session.execute('SELECT appointment_date FROM appointments')
    for row in result:
        print(row[0], type(row[0]))  # Print each appointment date and its type
