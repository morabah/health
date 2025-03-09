from health import create_app, db

app = create_app()

with app.app_context():
    result = db.session.execute('SELECT appointment_date FROM appointments')
    for row in result:
        print(row[0])  # Print each appointment date
