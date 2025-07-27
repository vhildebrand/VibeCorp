# User Authentication System
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import jwt

class AuthSystem:
    def __init__(self):
        self.users = {}
        self.secret_key = "your-secret-key"
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str, email: str) -> bool:
        if username in self.users:
            return False
        
        self.users[username] = {
            "password": self.hash_password(password),
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        return True
    
    def login_user(self, username: str, password: str) -> Optional[str]:
        user = self.users.get(username)
        if not user or user["password"] != self.hash_password(password):
            return None
        
        token = jwt.encode({
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }, self.secret_key, algorithm="HS256")
        
        return token
    
    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload["username"]
        except jwt.ExpiredSignatureError:
            return None