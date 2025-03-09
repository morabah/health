import os
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app import create_app
from fastapi_app import app as fastapi_app
from shared_session import SharedSessionManager
from errors import ErrorHandler
from flask import Flask

flask_app = create_app()

# Setup shared sessions
SharedSessionManager.setup_fastapi(fastapi_app)

# Mount static files for both Flask and FastAPI
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
fastapi_app.mount("/static", StaticFiles(directory=static_path), name="static")

# Add route for favicon.ico and apple-touch-icons at root level
@fastapi_app.get("/favicon.ico")
async def favicon():
    return fastapi.responses.FileResponse(os.path.join(static_path, "favicon.ico"))

@fastapi_app.get("/apple-touch-icon{rest:path}")
async def apple_touch_icon(rest: str):
    filename = f"apple-touch-icon{rest}"
    return fastapi.responses.FileResponse(os.path.join(static_path, filename))

# Setup Flask app
app = Flask(__name__)
# Setup session interface for sharing sessions with FastAPI
app.session_interface = SharedSessionManager.flask_session_interface()

# Register error handlers
@app.errorhandler(401)
def unauthorized(error):
    return ErrorHandler.handle_web_error('unauthorized')

@app.errorhandler(404)
def not_found(error):
    return ErrorHandler.handle_web_error('not_found')

@app.errorhandler(500)
def server_error(error):
    return ErrorHandler.handle_web_error('server_error')

@app.route('/')
def index():
    return 'Welcome to the Health Appointment App'

@app.route('/doctor/dashboard')
def doctor_dashboard():
    return 'Doctor Dashboard'

fastapi_app.mount("/flask", WSGIMiddleware(app))

# Add root redirect
@fastapi_app.get("/")
async def root():
    return RedirectResponse(url="/flask")

def run_flask_only():
    from app import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == "__main__":
    print('Starting Flask application only')
    run_flask_only()
