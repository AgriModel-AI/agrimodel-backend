import os
import time
from datetime import datetime, timedelta
from flask import jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Notification, db
from .tflite_inference import TFLitePlantDiseaseInferencePipeline

# Initialize TFLite model pipeline
pipeline = TFLitePlantDiseaseInferencePipeline(
    config_path='tflite_models/model_config.json'
)

# Temporary directory for storing images
TEMP_DIR = 'temp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure TEMP_DIR exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def allowed_file(filename):
    """Check if the uploaded file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class PredictionResource(Resource):
    @jwt_required()
    def post(self):
        """Handles image upload and plant disease prediction."""
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])

        # Validate image file
        image = request.files.get('image')
        if not image or not allowed_file(image.filename):
            return {"message": "A valid image file (png, jpg, jpeg, gif) is required."}, 400

        all_results = []
        start_time = time.time()

        try:
            # Save the file temporarily
            file_path = os.path.join(TEMP_DIR, image.filename)
            image.save(file_path)

            # Perform prediction
            result = pipeline.test_time_augmentation(file_path)

            # Add file info to result
            result['filename'] = image.filename
            all_results.append(result)

            # Remove temporary file
            os.remove(file_path)
        
        except Exception as e:
            all_results.append({
                'filename': image.filename,
                'error': f'Prediction error: {str(e)}'
            })

        # Calculate prediction time
        prediction_time = time.time() - start_time

        # Return response
        if len(all_results) == 1:
            result = all_results[0]
            result['prediction_time'] = f"{prediction_time:.3f} seconds"
            return jsonify(result)

        response = {
            'results': all_results,
            'prediction_time': f"{prediction_time:.3f} seconds",
            'count': len(all_results)
        }

        return jsonify(response)
