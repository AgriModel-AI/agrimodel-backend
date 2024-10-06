import os
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from routes import authBlueprint, mail, userDetailsBlueprint, communityBlueprint
from config import DevelopmentConfig
from models import db
from cli_commands import register_cli

migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not os.path.exists(config_class.UPLOAD_FOLDER):
        os.makedirs(config_class.UPLOAD_FOLDER)

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

    app.register_blueprint(authBlueprint)
    app.register_blueprint(userDetailsBlueprint)
    app.register_blueprint(communityBlueprint)

    register_cli(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
