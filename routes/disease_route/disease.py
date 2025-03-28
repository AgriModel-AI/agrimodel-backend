from flask import jsonify, request
from flask_restful import Resource, abort
from models import Crop, db, Disease
import cloudinary.uploader

# Allowed extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Utility function to check if a file is an allowed image type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                        # Upload the file to Cloudinary
                        upload_result = cloudinary.uploader.upload(file)

                        # Get the URL of the uploaded image
                        image_url = upload_result.get('url')
                    except Exception as e:
                        return {"message": f"Image upload failed: {str(e)}"}, 404
                    
                    images.append(image_url)
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
            images = []
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    
                    try:
                    # Upload the file to Cloudinary
                        upload_result = cloudinary.uploader.upload(file)

                        # Get the URL of the uploaded image
                        image_url = upload_result.get('url')
                    except Exception as e:
                        return {"message": f"Image upload failed: {str(e)}"}, 404
                    
                    images.append(image_url)
                    
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
            new_images = []
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    try:
                    # Upload the file to Cloudinary
                        upload_result = cloudinary.uploader.upload(file)

                        # Get the URL of the uploaded image
                        image_url = upload_result.get('url')
                    except Exception as e:
                        return {"message": f"Image upload failed: {str(e)}"}, 404
                    new_images.append(image_url)

            disease.images = ",".join(new_images)

        db.session.commit()
        return {"message": "Disease partially updated successfully."}, 200
    
    
    
    def delete(self):
        """Delete a disease entry."""
        disease_id = request.args.get("disease_id", type=int)
        disease = Disease.query.get(disease_id)
        if not disease:
            return {"message": "Disease not found."}, 404
        
        # Delete the disease record from the database
        db.session.delete(disease)
        db.session.commit()
        
        return {"message": "Disease deleted successfully."}, 200