import os
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from routes import authBlueprint, mail, socketio, userDetailsBlueprint, communityBlueprint, diseaseBlueprint, clientsBlueprint, supportBlueprint, dashboardBlueprint, diagnosisBlueprint, notificationBlueprint
from config import DevelopmentConfig
from models import db
from cli_commands import register_cli
from flask_cors import CORS

migrate = Migrate()
jwt = JWTManager()


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["SECRET_KEY"] = "CodeSpecialist.com"

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    if not os.path.exists(config_class.UPLOAD_FOLDER):
        os.makedirs(config_class.UPLOAD_FOLDER)
        
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
    # socketio.run(app, host='0.0.0.0', port=5000, debug=True)
