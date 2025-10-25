import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_padrao_para_dev')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Segurança de sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False if os.getenv('FLASK_DEBUG', '1') == '1' else True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOCK_MINUTES = 15
    
    # Debug
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'