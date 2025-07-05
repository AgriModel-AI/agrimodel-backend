import os
import logging
import cloudinary
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
# from routes import authBlueprint, mail, socketio, userDetailsBlueprint, communityBlueprint, diseaseBlueprint, cropBlueprint, clientsBlueprint, supportBlueprint, dashboardBlueprint, diagnosisBlueprint, notificationBlueprint
from routes import authBlueprint, mail, socketio, userDetailsBlueprint, communityBlueprint, diseaseBlueprint, cropBlueprint, clientsBlueprint, supportBlueprint, dashboardBlueprint, diagnosisBlueprint, notificationBlueprint, predictBlueprint
from config import DevelopmentConfig
from models import User, UserSubscription, db
from cli_commands import register_cli
from flask_cors import CORS
from flasgger import Swagger
import redis
from swagger_config import swagger_config, swagger_template
from flask_swagger_ui import get_swaggerui_blueprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

def create_app(config_class=DevelopmentConfig, allow=True):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["SECRET_KEY"] = "CodeSpecialist.com"
    
    # Add scheduler configuration
    app.config['SCHEDULER_API_ENABLED'] = False  # Set to True if you want to use the REST API
    app.config['SCHEDULER_PERSISTENT'] = True
    app.config['SUBSCRIPTION_CHECK_HOUR'] = 9
    app.config['SUBSCRIPTION_CHECK_MINUTE'] = 0
    app.config['SUBSCRIPTION_EXPIRY_HOUR'] = 0
    app.config['SUBSCRIPTION_EXPIRY_MINUTE'] = 5
    app.config['SCHEDULER_HEARTBEAT_MINUTES'] = 60

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    
    migrate = Migrate()
    jwt = JWTManager()
    
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
        
    CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "DELETE","POST", "PUT", "PATCH","OPTIONS"], allow_headers=["Content-Type", "Authorization"], supports_credentials=True)
    app.config['CORS_HEADERS'] = 'Content-Type'

    # Initialize Redis for distributed locking if available
    redis_client = None
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url)
            logging.info("Redis connected successfully for distributed locking")
        except Exception as e:
            logging.warning(f"Failed to connect to Redis: {str(e)}. Distributed locking will be disabled.")

    
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    
     # Setup Swagger UI
    SWAGGER_URL = '/api/v1/docs'  # URL for exposing Swagger UI
    API_URL = '/static/swagger/swagger.json'  # Where to find the Swagger JSON file
    
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "MY API DOCS"
        }
    )
    
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Register global error handler
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource Not Found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Not Processable"
        }), 422

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Server error"
        }), 500

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Initialize scheduler only in non-testing environments
    if allow:
        from scheduler import init_scheduler
        init_scheduler(app, mail, db, User, UserSubscription, redis_client)
        socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints (existing code)
    app.register_blueprint(authBlueprint)
    app.register_blueprint(userDetailsBlueprint)
    app.register_blueprint(communityBlueprint)
    app.register_blueprint(cropBlueprint)
    app.register_blueprint(diseaseBlueprint)
    app.register_blueprint(clientsBlueprint)
    app.register_blueprint(supportBlueprint)
    app.register_blueprint(dashboardBlueprint)
    app.register_blueprint(diagnosisBlueprint)
    app.register_blueprint(notificationBlueprint)
    app.register_blueprint(predictBlueprint)
    # app.register_blueprint(subscriptionBlueprint) 

    register_cli(app)

    return app

app = create_app()

if __name__ == "__main__":
    app = create_app()
    # app.run()
    socketio.run(app)