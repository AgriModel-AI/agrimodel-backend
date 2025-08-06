import os
import time
import logging
import uuid
from datetime import datetime
from flask import jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Crop, DiagnosisResult, Disease, Notification, UserDetails, db
from sqlalchemy import func
# import cloudinary.uploader
import cloudinary.uploader
from PIL import Image, UnidentifiedImageError
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
from werkzeug.exceptions import BadRequest
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BACKEND_URL = os.getenv('BACKEND_URL')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model and config
class_names = [
    'Unknown',
    'black_sigatoka',
    'healthly_banana',
    'healthly_coffee',
    'leaf_rust',
    'yellow_sigatoka'
]

try:
    model = torch.jit.load("models_storage/agri_model_mobile.pt")
    model.to("cpu")
    model.eval()
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    model = None

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.4141, 0.4764, 0.2334], std=[0.2762, 0.2792, 0.2551])
])

TEMP_DIR = 'temp'
UPLOADS_DIR = 'static/uploads/images'  # Changed to static folder for serving via Flask
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create necessary directories
for directory in [TEMP_DIR, UPLOADS_DIR]:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {str(e)}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def predict_image_pytorch(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        input_tensor = transform(image).unsqueeze(0)
        
        if model is None:
            raise ValueError("Model is not loaded")
            
        with torch.no_grad():
            output = model(input_tensor)
            probabilities = F.softmax(output, dim=1)
            predicted_class = torch.argmax(output, dim=1)
            confidence = probabilities[0, predicted_class].item()

        predicted_label = class_names[predicted_class]
        
        print(predicted_label)

        if predicted_label == 'healthly_banana':
            return {'plant_type': 'banana', 'disease_status': 'Healthy'}
        elif predicted_label == 'healthly_coffee':
            return {'plant_type': 'coffee', 'disease_status': 'Healthy'}
        elif predicted_label in ['black_sigatoka', 'yellow_sigatoka']:
            return {'plant_type': 'banana', 'disease_status': predicted_label}
        elif predicted_label in ['leaf_rust']:
            return {'plant_type': 'coffee', 'disease_status': predicted_label}
        else:
            return {'plant_type': 'unknown', 'disease_status': 'unknown'}
    except UnidentifiedImageError:
        logger.error(f"Could not identify image file: {image_path}")
        raise ValueError("The provided file is not a valid image")
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        raise

class PredictionResource(Resource):
    @jwt_required()
    def post(self):
        temp_file_path = None
        
        try:
            # Get user identity
            user_identity = get_jwt_identity()
            userId = int(user_identity["userId"])
            modelVersion = "1.0.2"

            # Validate image file
            if 'image' not in request.files:
                return {"message": "No image file provided"}, 400
                
            image = request.files.get('image')
            if not image or not image.filename:
                return {"message": "Empty image file provided"}, 400
                
            if not allowed_file(image.filename):
                return {"message": "File format not supported. Please upload png, jpg, jpeg, or gif."}, 400

            # Save file temporarily
            filename = image.filename
            extension = filename.rsplit('.', 1)[1].lower()
            temp_file_path = os.path.join(TEMP_DIR, filename)
            image.save(temp_file_path)

            # Process image and get prediction
            start_time = time.time()
            result = predict_image_pytorch(temp_file_path)
            prediction_time = time.time() - start_time

            # Prepare response
            response = {
                "detected": result["plant_type"] in ['banana', 'coffee'],
                "disease_status": result["disease_status"],
                "plant_type": result["plant_type"],
                "prediction_time": f"{prediction_time:.3f} seconds",
                "model_version": modelVersion,
                "rated": False
            }

            # If valid plant type detected, get additional data
            if result["plant_type"] in ['banana', 'coffee']:
                # Get crop information
                crop_name = result["plant_type"].capitalize()
                crop = Crop.query.filter(func.lower(Crop.name) == func.lower(crop_name)).first()

                if crop:
                    response["cropId"] = crop.cropId
                    response["cropName"] = crop.name
                    
                    # Get disease information
                    try:
                        disease = Disease.query.filter_by(cropId=crop.cropId, label=result["disease_status"]).first()
                        
                        if disease:
                            response.update({
                                "diseaseId": disease.diseaseId,
                                "diseaseName": disease.name,
                                "diseaseDescription": disease.description,
                                "diseaseLabel": disease.label,
                                "diseaseSymptoms": disease.symptoms,
                                "diseaseTreatment": disease.treatment,
                                "diseasePrevention": disease.prevention,
                                "relatedDiseases": disease.relatedDiseases.split(",") if disease.relatedDiseases else []
                            })

                            # Get user district
                            try:
                                user_details = UserDetails.query.filter_by(userId=userId).first()
                                districtId = user_details.districtId if user_details else None
                            except Exception as e:
                                logger.warning(f"Failed to get user district: {str(e)}")
                                districtId = None

                            # Generate a unique filename for permanent storage
                            unique_filename = f"{uuid.uuid4().hex}.{extension}"
                            permanent_file_path = os.path.join(UPLOADS_DIR, unique_filename)
                            
                            # Save file to permanent storage
                            try:
                                # Copy the file to permanent location
                                shutil.copy2(temp_file_path, permanent_file_path)
                                
                                # Construct URL using BACKEND_URL from environment
                                # Ensure BACKEND_URL ends with a slash
                                if not BACKEND_URL.endswith('/'):
                                    backend_url = BACKEND_URL + '/'
                                else:
                                    backend_url = BACKEND_URL
                                
                                image_url = f"{backend_url}static/uploads/images/{unique_filename}"
                                response["image_url"] = image_url
                                
                                # Cloudinary upload code (commented out but preserved)
                                """
                                upload_result = cloudinary.uploader.upload(temp_file_path)
                                image_url = upload_result.get('url')
                                response["image_url"] = image_url
                                """
                            except Exception as e:
                                logger.error(f"File storage failed: {str(e)}")
                                raise ValueError("Failed to save image to storage")

                            # Save diagnosis result to database
                            try:
                                new_diagnosis = DiagnosisResult(
                                    userId=userId,
                                    diseaseId=disease.diseaseId,
                                    districtId=districtId,
                                    date=datetime.utcnow(),
                                    image_path=image_url,  # Use constructed URL
                                    detected=True,
                                    modelVersion=modelVersion,
                                    rated=False
                                )
                                db.session.add(new_diagnosis)
                                db.session.commit()
                            except Exception as e:
                                db.session.rollback()
                                logger.error(f"Database operation failed: {str(e)}")
                                raise ValueError("Failed to save diagnosis result to database")
                    except Exception as e:
                        logger.error(f"Error processing disease data: {str(e)}")
                        # Continue with partial response rather than failing completely

            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
            return jsonify(response)

        except ValueError as e:
            # Handle known validation errors
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return {"message": str(e)}, 400
            
        except BadRequest as e:
            # Handle request parsing errors
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return {"message": "Invalid request: " + str(e)}, 400
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error in prediction API: {str(e)}", exc_info=True)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return {"message": "An unexpected error occurred during processing"}, 500