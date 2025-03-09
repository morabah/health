from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Create all tables based on current models
    db.create_all()
    
    # Create alembic_version table using a connection
    with db.engine.connect() as connection:
        connection.execute(text('CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)'))
    print("Migration reset completed.")
