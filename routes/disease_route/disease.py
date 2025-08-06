# from flask import jsonify, request
# from flask_restful import Resource, abort
# from models import Crop, db, Disease
# import cloudinary.uploader

# # Allowed extensions for images
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# # Utility function to check if a file is an allowed image type
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# # Helper validation functions
# def validate_required_field(value, field_name):
#     if not value or not value.strip():
#         abort(400, message=f"{field_name} is required.")

# def validate_min_length(value, field_name, min_length):
#     if len(value.strip()) < min_length:
#         abort(400, message=f"{field_name} must be at least {min_length} characters long.")
        
# def validate_crop_exists(crop_id):
#     crop = Crop.query.get(crop_id)
#     if not crop:
#         abort(400, message=f"Crop with ID {crop_id} does not exist.")
#     return crop
        
# class DiseaseResource(Resource):
    
#     def get(self, disease_id=None):
#         """Retrieve a single disease or list all diseases"""
#         if disease_id:
#             disease = Disease.query.get(disease_id)
#             if not disease:
#                 return {"message": "Disease not found."}, 404
#             return jsonify(disease.serialize())  # Assuming Disease model has a serialize() method
#         else:
#             diseases = Disease.query.all()
#             return {"data": [disease.serialize() for disease in diseases]}, 200
         
#     def post(self):
#         """Create a new disease entry with multiple image uploads."""
#         data = request.form
#         name = data.get("name")
#         description = data.get("description")
#         label = data.get("label")
#         symptoms = data.get("symptoms")
#         treatment = data.get("treatment")
#         prevention = data.get("prevention")
#         crop_id = data.get("cropId")
#         images = []

#         # Validation
#         validate_required_field(name, "Disease name")
#         validate_min_length(name, "Disease name", 3)
#         validate_required_field(description, "Description")
#         validate_required_field(label, "Label")
#         validate_required_field(crop_id, "Crop ID")
#         validate_crop_exists(crop_id)

#         # Handle image uploads
#         if 'images' in request.files:
#             uploaded_files = request.files.getlist("images")
#             for file in uploaded_files:
#                 if file and allowed_file(file.filename):
                    
#                     try:
#                         # Upload the file to Cloudinary
#                         upload_result = cloudinary.uploader.upload(file)

#                         # Get the URL of the uploaded image
#                         image_url = upload_result.get('url')
#                     except Exception as e:
#                         return {"message": f"Image upload failed: {str(e)}"}, 404
                    
#                     images.append(image_url)
#                 else:
#                     return {"message": "Invalid file format. Allowed types: png, jpg, jpeg, gif."}, 400

#         # Store image paths as comma-separated string
#         image_paths = ",".join(images)

#         # Create new disease entry
#         new_disease = Disease(
#             name=name,
#             description=description,
#             label=label,
#             symptoms=symptoms,
#             treatment=treatment,
#             prevention=prevention,
#             cropId=crop_id,
#             images=image_paths
#         )
#         db.session.add(new_disease)
#         db.session.commit()

#         return {"message": "Disease created successfully.", "disease_id": new_disease.diseaseId}, 201

#     def put(self):
#         """Update an entire disease entry."""
#         disease_id = request.args.get("disease_id", type=int)
#         disease = Disease.query.get(disease_id)
#         if not disease:
#             return {"message": "Disease not found."}, 404

#         data = request.form
#         name = data.get("name")
#         description = data.get("description")
#         label = data.get("label")
#         symptoms = data.get("symptoms")
#         treatment = data.get("treatment")
#         prevention = data.get("prevention")
#         crop_id = data.get("cropId")

#         # Validation
#         validate_required_field(name, "Disease name")
#         validate_min_length(name, "Disease name", 3)
#         validate_required_field(description, "Description")
#         validate_required_field(label, "Label")
#         validate_required_field(crop_id, "Crop ID")
#         validate_crop_exists(crop_id)

#         # Update fields
#         disease.name = name
#         disease.description = description
#         disease.label = label
#         disease.symptoms = symptoms
#         disease.treatment = treatment
#         disease.prevention = prevention
#         disease.cropId = crop_id
        

#         # Handle replacing images if new images are provided
#         if 'images' in request.files:
#             uploaded_files = request.files.getlist("images")
#             images = []
#             for file in uploaded_files:
#                 if file and allowed_file(file.filename):
                    
#                     try:
#                     # Upload the file to Cloudinary
#                         upload_result = cloudinary.uploader.upload(file)

#                         # Get the URL of the uploaded image
#                         image_url = upload_result.get('url')
#                     except Exception as e:
#                         return {"message": f"Image upload failed: {str(e)}"}, 404
                    
#                     images.append(image_url)
                    
#             disease.images = ",".join(images)  # Replace all images

#         db.session.commit()
#         return {"message": "Disease updated successfully."}, 200

#     def patch(self):
#         """Partially update a disease entry."""
#         disease_id = request.args.get("disease_id", type=int)
#         disease = Disease.query.get(disease_id)
#         if not disease:
#             return {"message": "Disease not found."}, 404

#         data = request.form
#         if "name" in data:
#             name = data["name"]
#             validate_min_length(name, "Disease name", 3)
#             disease.name = name

#         if "description" in data:
#             description = data["description"]
#             disease.description = description
            
#         if "label" in data:
#             label = data["label"]
#             disease.label = label
            
#         if "cropId" in data:
#             cropId = data["cropId"]
#             disease.cropId = cropId

#         if "symptoms" in data:
#             symptoms = data["symptoms"]
#             disease.symptoms = symptoms

#         if "treatment" in data:
#             treatment = data["treatment"]
#             disease.treatment = treatment

#         if "prevention" in data:
#             prevention = data["prevention"]
#             disease.prevention = prevention

#         # Append new images to existing images if provided
#         if 'images' in request.files:
#             uploaded_files = request.files.getlist("images")
#             new_images = []
#             for file in uploaded_files:
#                 if file and allowed_file(file.filename):
#                     try:
#                     # Upload the file to Cloudinary
#                         upload_result = cloudinary.uploader.upload(file)

#                         # Get the URL of the uploaded image
#                         image_url = upload_result.get('url')
#                     except Exception as e:
#                         return {"message": f"Image upload failed: {str(e)}"}, 404
#                     new_images.append(image_url)

#             disease.images = ",".join(new_images)

#         db.session.commit()
#         return {"message": "Disease partially updated successfully."}, 200
    
    
    
#     def delete(self):
#         """Delete a disease entry."""
#         disease_id = request.args.get("disease_id", type=int)
#         disease = Disease.query.get(disease_id)
#         if not disease:
#             return {"message": "Disease not found."}, 404
        
#         # Delete the disease record from the database
#         db.session.delete(disease)
#         db.session.commit()
        
#         return {"message": "Disease deleted successfully."}, 200


import os
import uuid
import logging
from flask import jsonify, request
from flask_restful import Resource, abort
from models import Crop, db, Disease
# Keep the import for future reference
import cloudinary.uploader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BACKEND_URL = os.getenv('BACKEND_URL')
if not BACKEND_URL.endswith('/'):
    BACKEND_URL += '/'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up storage directories
UPLOADS_DIR = 'static/uploads/diseases'
if not os.path.exists(UPLOADS_DIR):
    try:
        os.makedirs(UPLOADS_DIR)
    except OSError as e:
        logger.error(f"Failed to create directory {UPLOADS_DIR}: {str(e)}")

# Allowed extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Utility function to check if a file is an allowed image type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to save image locally
def save_image_locally(file):
    """Save image to local storage and return URL"""
    if not file:
        return None
        
    # Generate unique filename
    original_filename = file.filename
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Save file
    file_path = os.path.join(UPLOADS_DIR, unique_filename)
    file.save(file_path)
    
    # Create URL using BACKEND_URL
    relative_path = f"static/uploads/diseases/{unique_filename}"
    return f"{BACKEND_URL}{relative_path}"

# Helper function to delete image from local storage
def delete_image_locally(image_url):
    """Delete image from local storage"""
    if not image_url or not image_url.startswith(BACKEND_URL):
        return False
    
    try:
        # Extract the file path from the URL
        relative_path = image_url.replace(BACKEND_URL, '')
        file_path = os.path.join(os.getcwd(), relative_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        logger.error(f"Failed to delete image: {str(e)}")
    
    return False

# Helper validation functions
def validate_required_field(value, field_name):
    if not value or not value.strip():
        abort(400, message=f"{field_name} is required.")

def validate_min_length(value, field_name, min_length):
    if len(value.strip()) < min_length:
        abort(400, message=f"{field_name} must be at least {min_length} characters long.")
        
def validate_crop_exists(crop_id):
    crop = Crop.query.get(crop_id)
    if not crop:
        abort(400, message=f"Crop with ID {crop_id} does not exist.")
    return crop
        
class DiseaseResource(Resource):
    
    def get(self, disease_id=None):
        """Retrieve a single disease or list all diseases"""
        if disease_id:
            disease = Disease.query.get(disease_id)
            if not disease:
                return {"message": "Disease not found."}, 404
            return jsonify(disease.serialize())  # Assuming Disease model has a serialize() method
        else:
            diseases = Disease.query.all()
            return {"data": [disease.serialize() for disease in diseases]}, 200
         
    def post(self):
        """Create a new disease entry with multiple image uploads."""
        data = request.form
        name = data.get("name")
        description = data.get("description")
        label = data.get("label")
        symptoms = data.get("symptoms")
        treatment = data.get("treatment")
        prevention = data.get("prevention")
        crop_id = data.get("cropId")
        images = []

        # Validation
        validate_required_field(name, "Disease name")
        validate_min_length(name, "Disease name", 3)
        validate_required_field(description, "Description")
        validate_required_field(label, "Label")
        validate_required_field(crop_id, "Crop ID")
        validate_crop_exists(crop_id)

        # Handle image uploads
        if 'images' in request.files:
            uploaded_files = request.files.getlist("images")
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    try:
                        # Save the file to local storage
                        image_url = save_image_locally(file)
                        images.append(image_url)
                        
                        # Cloudinary upload code (commented out but preserved)
                        """
                        # Upload the file to Cloudinary
                        upload_result = cloudinary.uploader.upload(file)
                        # Get the URL of the uploaded image
                        image_url = upload_result.get('url')
                        images.append(image_url)
                        """
                    except Exception as e:
                        logger.error(f"Image upload failed: {str(e)}")
                        return {"message": f"Image upload failed: {str(e)}"}, 500
                else:
                    return {"message": "Invalid file format. Allowed types: png, jpg, jpeg, gif."}, 400

        # Store image paths as comma-separated string
        image_paths = ",".join(images)

        # Create new disease entry
        new_disease = Disease(
            name=name,
            description=description,
            label=label,
            symptoms=symptoms,
            treatment=treatment,
            prevention=prevention,
            cropId=crop_id,
            images=image_paths
        )
        db.session.add(new_disease)
        db.session.commit()

        return {"message": "Disease created successfully.", "disease_id": new_disease.diseaseId}, 201

    def put(self):
        """Update an entire disease entry."""
        disease_id = request.args.get("disease_id", type=int)
        disease = Disease.query.get(disease_id)
        if not disease:
            return {"message": "Disease not found."}, 404

        data = request.form
        name = data.get("name")
        description = data.get("description")
        label = data.get("label")
        symptoms = data.get("symptoms")
        treatment = data.get("treatment")
        prevention = data.get("prevention")
        crop_id = data.get("cropId")

        # Validation
        validate_required_field(name, "Disease name")
        validate_min_length(name, "Disease name", 3)
        validate_required_field(description, "Description")
        validate_required_field(label, "Label")
        validate_required_field(crop_id, "Crop ID")
        validate_crop_exists(crop_id)

        # Update fields
        disease.name = name
        disease.description = description
        disease.label = label
        disease.symptoms = symptoms
        disease.treatment = treatment
        disease.prevention = prevention
        disease.cropId = crop_id
        

        # Handle replacing images if new images are provided
        if 'images' in request.files:
            uploaded_files = request.files.getlist("images")
            
            # Delete old images from storage
            if disease.images:
                old_image_urls = disease.images.split(",")
                for old_url in old_image_urls:
                    delete_image_locally(old_url)
            
            # Upload new images
            images = []
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    try:
                        # Save the file to local storage
                        image_url = save_image_locally(file)
                        images.append(image_url)
                        
                        # Cloudinary upload code (commented out but preserved)
                        """
                        # Upload the file to Cloudinary
                        upload_result = cloudinary.uploader.upload(file)
                        # Get the URL of the uploaded image
                        image_url = upload_result.get('url')
                        images.append(image_url)
                        """
                    except Exception as e:
                        logger.error(f"Image upload failed: {str(e)}")
                        return {"message": f"Image upload failed: {str(e)}"}, 500
                    
            disease.images = ",".join(images)  # Replace all images

        db.session.commit()
        return {"message": "Disease updated successfully."}, 200

    def patch(self):
        """Partially update a disease entry."""
        disease_id = request.args.get("disease_id", type=int)
        disease = Disease.query.get(disease_id)
        if not disease:
            return {"message": "Disease not found."}, 404

        data = request.form
        if "name" in data:
            name = data["name"]
            validate_min_length(name, "Disease name", 3)
            disease.name = name

        if "description" in data:
            description = data["description"]
            disease.description = description
            
        if "label" in data:
            label = data["label"]
            disease.label = label
            
        if "cropId" in data:
            cropId = data["cropId"]
            disease.cropId = cropId

        if "symptoms" in data:
            symptoms = data["symptoms"]
            disease.symptoms = symptoms

        if "treatment" in data:
            treatment = data["treatment"]
            disease.treatment = treatment

        if "prevention" in data:
            prevention = data["prevention"]
            disease.prevention = prevention

        # Append new images to existing images if provided
        if 'images' in request.files:
            uploaded_files = request.files.getlist("images")
            
            # Get existing images if any
            existing_images = []
            if disease.images:
                existing_images = disease.images.split(",")
            
            # Upload new images
            new_images = []
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    try:
                        # Save the file to local storage
                        image_url = save_image_locally(file)
                        new_images.append(image_url)
                        
                        # Cloudinary upload code (commented out but preserved)
                        """
                        # Upload the file to Cloudinary
                        upload_result = cloudinary.uploader.upload(file)
                        # Get the URL of the uploaded image
                        image_url = upload_result.get('url')
                        new_images.append(image_url)
                        """
                    except Exception as e:
                        logger.error(f"Image upload failed: {str(e)}")
                        return {"message": f"Image upload failed: {str(e)}"}, 500
            
            # Combine existing and new images
            all_images = existing_images + new_images
            disease.images = ",".join(all_images)

        db.session.commit()
        return {"message": "Disease partially updated successfully."}, 200
    
    def delete(self):
        """Delete a disease entry."""
        disease_id = request.args.get("disease_id", type=int)
        disease = Disease.query.get(disease_id)
        if not disease:
            return {"message": "Disease not found."}, 404
        
        # Delete associated images from storage
        if disease.images:
            image_urls = disease.images.split(",")
            for url in image_urls:
                delete_image_locally(url)
                
                # Cloudinary deletion code (commented out but preserved)
                """
                try:
                    public_id = url.strip().split("/")[-1].split(".")[0]
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    logger.error(f"Failed to delete image from Cloudinary: {str(e)}")
                """
        
        # Delete the disease record from the database
        db.session.delete(disease)
        db.session.commit()
        
        return {"message": "Disease deleted successfully."}, 200