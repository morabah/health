from flask_migrate import Migrate
from app import create_app
from models import db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    # This script can be run directly to initialize migrations
    # Run: python migrations.py db init
    # Then: python migrations.py db migrate
    # Then: python migrations.py db upgrade
    from flask_migrate import Manager
    
    manager = Manager(app)
    manager.run()
