# config.py
from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=45)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Image upload configurations
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')  # Default folder for uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image types
    BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    DISEASES_UPLOAD_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, 'diseases')
    
    @staticmethod
    def allowed_file(filename):
        """Check if the uploaded file has a valid extension."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

class TestingConfig(Config):
    TESTING = True
    SERVER_NAME = None
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL")

config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}


os.makedirs(Config.BASE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.DISEASES_UPLOAD_FOLDER, exist_ok=True)