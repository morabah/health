import bcrypt
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_password():
    stored_hash = '$2b$12$oYpQJMJ8tHbxEzIevC53g.V363NKuRhCGLDEMOZ8rL37rMmiklP6.'
    password = 'Dd123456'
    
    logger.info(f"Testing bcrypt.checkpw for password: {password}")
    logger.info(f"Hash: {stored_hash}")
    
    try:
        # bcrypt.checkpw expects bytes
        password_bytes = password.encode('utf-8')
        stored_hash_bytes = stored_hash.encode('utf-8')
        
        logger.info(f"password_bytes: {password_bytes}")
        logger.info(f"stored_hash_bytes: {stored_hash_bytes}")
        
        # Check if the password matches the hash
        result = bcrypt.checkpw(password_bytes, stored_hash_bytes)
        logger.info(f"bcrypt result: {result}")
        return result
    except Exception as e:
        logger.error(f"Bcrypt error: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_password()
    print(f"Final result: {result}")
