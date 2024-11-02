from flask import current_app, send_from_directory, abort
from flask_restful import Api, Resource, abort

class DiseaseSingleImageResource(Resource):
    def get(self, filename):
        """Serve an individual image by filename."""
        image_directory = current_app.config["DISEASES_UPLOAD_FOLDER"]
        try:
            return send_from_directory(image_directory, filename)
        except FileNotFoundError:
            abort(404, description="Image not found.")
