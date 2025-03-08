import os
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import RedirectResponse
from app import create_app
from fastapi_app import app as fastapi_app

flask_app = create_app()

fastapi_app.mount("/flask", WSGIMiddleware(flask_app))

# Add root redirect
@fastapi_app.get("/")
async def root():
    return RedirectResponse(url="/flask")

def run_flask():
    os.system("gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --limit-request-field_size 8190 app:create_app")

if __name__ == "__main__":
    print("Starting hybrid application (Flask + FastAPI)")
    print("Flask running on http://localhost:5000")
    print("FastAPI running on http://localhost:8000")
    print("FastAPI Swagger docs at http://localhost:8000/docs")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Run FastAPI in the main thread
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, 
                headers=[('server', 'Uvicorn'), ('limit_request_fields', '1000')])
