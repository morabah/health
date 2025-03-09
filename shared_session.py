import json
from datetime import datetime, timedelta
import redis
import secrets
import uuid
from flask import session as flask_session
from starlette.middleware.sessions import SessionMiddleware

# Configure Redis for session storage
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class SharedSessionManager:
    SESSION_EXPIRY = 86400  # 24 hours in seconds
    
    @staticmethod
    def generate_session_id():
        return str(uuid.uuid4())
    
    @staticmethod
    def store_session(session_id, data):
        redis_client.setex(
            f"session:{session_id}", 
            SharedSessionManager.SESSION_EXPIRY,
            json.dumps(data)
        )
        return session_id
    
    @staticmethod
    def get_session(session_id):
        data = redis_client.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return None
    
    @staticmethod
    def delete_session(session_id):
        redis_client.delete(f"session:{session_id}")
    
    @staticmethod
    def setup_fastapi(app):
        """Add session middleware to FastAPI app"""
        app.add_middleware(
            SessionMiddleware, 
            secret_key=secrets.token_hex(16),
            session_cookie="health_session",
            max_age=SharedSessionManager.SESSION_EXPIRY
        )
    
    @staticmethod
    def flask_session_interface():
        """Custom session interface for Flask"""
        from flask.sessions import SessionInterface, SessionMixin
        
        class RedisSession(dict, SessionMixin):
            def __init__(self, session_id, data=None):
                self.session_id = session_id
                self.modified = False
                self.accessed = False
                super(RedisSession, self).__init__(data or {})
        
        class RedisSessionInterface(SessionInterface):
            def open_session(self, app, request):
                session_id = request.cookies.get('health_session')
                if not session_id:
                    session_id = SharedSessionManager.generate_session_id()
                    return RedisSession(session_id)
                
                data = SharedSessionManager.get_session(session_id)
                if data is not None:
                    return RedisSession(session_id, data)
                return RedisSession(session_id)
            
            def save_session(self, app, session, response):
                domain = self.get_cookie_domain(app)
                path = self.get_cookie_path(app)
                
                if not session:
                    if session.modified:
                        SharedSessionManager.delete_session(session.session_id)
                        response.delete_cookie('health_session', domain=domain, path=path)
                    return
                
                if session.modified:
                    SharedSessionManager.store_session(session.session_id, dict(session))
                
                response.set_cookie(
                    'health_session',
                    session.session_id,
                    max_age=SharedSessionManager.SESSION_EXPIRY,
                    path=path,
                    domain=domain,
                    secure=app.config.get('SESSION_COOKIE_SECURE', False),
                    httponly=True
                )
        
        return RedisSessionInterface()
