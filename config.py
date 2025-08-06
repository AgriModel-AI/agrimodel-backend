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
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=60)
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
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload size
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Static file serving configuration
    STATIC_FOLDER = 'static'
    STATIC_CACHE_TIMEOUT = 2592000  # 30 days in seconds
    
    # Backend URL for constructing image URLs
    BACKEND_URL = os.environ.get('BACKEND_URL', 'http://172.20.10.2:5000/')
    
    # Uploads directory structure
    UPLOAD_FOLDERS = {
        'posts': 'static/uploads/posts',
        'communities': 'static/uploads/communities',
        'diseases': 'static/uploads/diseases',
        'explore': 'static/uploads/explore',
        'diagnosis': 'static/uploads/images'
    }
    
    @staticmethod
    def allowed_file(filename):
        """Check if the uploaded file has a valid extension."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Create upload directories if they don't exist
        for folder in Config.UPLOAD_FOLDERS.values():
            os.makedirs(folder, exist_ok=True)
        
        # Configure static file serving
        @app.route('/static/<path:filename>')
        def static_files(filename):
            response = app.send_static_file(filename)
            cache_timeout = app.config.get('STATIC_CACHE_TIMEOUT', 2592000)
            response.headers['Cache-Control'] = f'public, max-age={cache_timeout}'
            return response
        
        # Special route for uploaded files
        @app.route('/static/uploads/<path:subpath>')
        def uploaded_files(subpath):
            directory = os.path.dirname(os.path.join('static/uploads', subpath))
            filename = os.path.basename(subpath)
            response = app.send_from_directory(directory, filename)
            cache_timeout = app.config.get('STATIC_CACHE_TIMEOUT', 2592000)
            response.headers['Cache-Control'] = f'public, max-age={cache_timeout}'
            return response

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

class TestingConfig(Config):
    TESTING = True
    SERVER_NAME = None
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL")

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False  # Set to False for production
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_ECHO = False  # Set to False for production
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Add production-specific security headers
        @app.after_request
        def set_secure_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response

config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}