from cryptography.fernet import Fernet
from .config import Config
import jwt
from datetime import datetime, timedelta, timezone
import base64

secret = Config.SECRET_KEY
cipher = Fernet(base64.urlsafe_b64encode(secret.ljust(32)[:32]))
    

def crypt_password(password: str) -> str:
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(token: str) -> str:
    return cipher.decrypt(token.encode()).decode()

def generate_token(payload: dict) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(weeks=1)
    
    payload.update({"exp": expires_at})
    
    token = jwt.encode(payload, key=secret, algorithm='HS256')
    return token

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, key=secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {}
    except jwt.InvalidTokenError:
        return {}
    