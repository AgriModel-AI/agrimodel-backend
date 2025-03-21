import os
import time
from datetime import datetime, timedelta
from flask import jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Crop, DiagnosisResult, Disease, Notification, UserDetails, db
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

# class PredictionResource(Resource):
#     @jwt_required()
#     def post(self):
#         """Handles image upload and plant disease prediction."""
#         user_identity = get_jwt_identity()
#         userId = int(user_identity["userId"])

#         # Validate image file
#         image = request.files.get('image')
#         if not image or not allowed_file(image.filename):
#             return {"message": "A valid image file (png, jpg, jpeg, gif) is required."}, 400

#         all_results = []
#         start_time = time.time()

#         try:
#             # Save the file temporarily
#             file_path = os.path.join(TEMP_DIR, image.filename)
#             image.save(file_path)

#             # Perform prediction
#             result = pipeline.test_time_augmentation(file_path)

#             # Add file info to result
#             result['filename'] = image.filename
#             all_results.append(result)

#             # Remove temporary file
#             os.remove(file_path)
        
#         except Exception as e:
#             all_results.append({
#                 'filename': image.filename,
#                 'error': f'Prediction error: {str(e)}'
#             })

#         # Calculate prediction time
#         prediction_time = time.time() - start_time

#         # Return response
#         # if len(all_results) == 1:
#         #     result = all_results[0]
#         #     result['prediction_time'] = f"{prediction_time:.3f} seconds"
#         #     return jsonify(result)

#         # response = {
#         #     'results': all_results,
#         #     'prediction_time': f"{prediction_time:.3f} seconds",
#         #     'count': len(all_results)
#         # }
        
#         response = {
#             "detected": all_results[0]["plant_type"] in ['banana', 'coffee'],
#             "disease_status": all_results[0]["disease_status"],
#             "plant_type": all_results[0]["plant_type"],
#             "prediction_time" : f"{prediction_time:.3f} seconds",
#         }
        

#         return jsonify(response)


from sqlalchemy import func
import cloudinary.uploader

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

        file_path = os.path.join(TEMP_DIR, image.filename)
        
        try:
            # Save the file temporarily
            image.save(file_path)

            # Perform prediction
            start_time = time.time()
            result = pipeline.test_time_augmentation(file_path)
            prediction_time = time.time() - start_time

            # Initial response with basic prediction info
            response = {
                "detected": result["plant_type"] in ['banana', 'coffee'],
                "disease_status": result["disease_status"],
                "plant_type": result["plant_type"],
                "prediction_time": f"{prediction_time:.3f} seconds",
            }
            
            # If detected plant is banana or coffee, proceed with database operations
            if result["plant_type"] in ['banana', 'coffee']:
                # Look up crop in database (case-insensitive search)
                crop_name = result["plant_type"].capitalize()
                crop = Crop.query.filter(func.lower(Crop.name) == func.lower(crop_name)).first()
                
                if crop:
                    # Add crop info to response
                    response["cropId"] = crop.cropId
                    response["cropName"] = crop.name
                    
                    # Look up disease by crop ID and label
                    disease = Disease.query.filter_by(
                        cropId=crop.cropId, 
                        label=result["disease_status"]
                    ).first()
                    
                    if disease:
                        # Add disease info to response
                        response["diseaseId"] = disease.diseaseId
                        response["diseaseName"] = disease.name
                        response["diseaseDescription"] = disease.description
                        response["diseaseLabel"] = disease.label
                        response["diseaseSymptoms"] = disease.symptoms
                        response["diseaseTreatment"] = disease.treatment
                        response["diseasePrevention"] = disease.prevention
                        response["relatedDiseases"] = disease.relatedDiseases.split(",") if disease.relatedDiseases else []
                        
                        # Get user's district ID from UserDetails
                        user_details = UserDetails.query.filter_by(userId=userId).first()
                        districtId = user_details.districtId if user_details else None
                        
                        # Upload the file to Cloudinary
                        upload_result = cloudinary.uploader.upload(file_path)

                        # Get the URL of the uploaded image
                        image_url = upload_result.get('url')
                        
                        # Add image URL to response
                        response["image_url"] = image_url
                        
                        # Create and save new DiagnosisResult
                        new_diagnosis = DiagnosisResult(
                            userId=userId,
                            diseaseId=disease.diseaseId,
                            districtId=districtId,
                            date=datetime.utcnow(),
                            image_path=image_url,
                            detected=True
                        )
                        db.session.add(new_diagnosis)
                        db.session.commit()
            
            # Remove temporary file
            os.remove(file_path)
            
            return jsonify(response)
        
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return {
                'error': f'Prediction error: {str(e)}'
            }, 500