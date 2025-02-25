import os
import cloudinary
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from routes import authBlueprint, mail, socketio, userDetailsBlueprint, communityBlueprint, diseaseBlueprint, clientsBlueprint, supportBlueprint, dashboardBlueprint, diagnosisBlueprint, notificationBlueprint
from config import DevelopmentConfig
from models import db
from cli_commands import register_cli
from flask_cors import CORS



def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["SECRET_KEY"] = "CodeSpecialist.com"

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    
    migrate = Migrate()
    jwt = JWTManager()
    
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
        
    CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "DELETE","POST", "PUT", "PATCH","OPTIONS"], allow_headers=["Content-Type", "Authorization"], supports_credentials=True)

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
    socketio.init_app(app, cors_allowed_origins="*")

    app.register_blueprint(authBlueprint)
    app.register_blueprint(userDetailsBlueprint)
    app.register_blueprint(communityBlueprint)
    app.register_blueprint(diseaseBlueprint)
    app.register_blueprint(clientsBlueprint)
    app.register_blueprint(supportBlueprint)
    app.register_blueprint(dashboardBlueprint)
    app.register_blueprint(diagnosisBlueprint)
    app.register_blueprint(notificationBlueprint)

    register_cli(app)

    return app

app = create_app()

if __name__ == "__main__":
    app = create_app()
    # app.run()
    socketio.run(app)
