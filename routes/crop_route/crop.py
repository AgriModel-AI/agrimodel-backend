from flask import jsonify, request
from flask_restful import Resource, abort
from models import db, Crop
import cloudinary.uploader

# Allowed extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

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
        
        
class CropResource(Resource):
    
    def get(self, crop_id=None):
        """Retrieve a single crop or list all crops"""
        if crop_id:
            crop = Crop.query.get(crop_id)
            if not crop:
                return {"message": "Crop not found."}, 404
            return jsonify(crop.serialize())
        else:
            crops = Crop.query.all()
            return {"data": [crop.serialize() for crop in crops]}, 200
         
    def post(self):
        """Create a new crop entry with multiple image uploads."""
        data = request.form
        name = data.get("name")
        description = data.get("description")
        growing_conditions = data.get("growingConditions")
        harvest_time = data.get("harvestTime")
        images = []

        # Validation
        validate_required_field(name, "Crop name")
        validate_min_length(name, "Crop name", 3)
        validate_required_field(description, "Description")

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
                    return {"message": "Invalid file format. Allowed types: png, jpg, jpeg, gif, webp."}, 400

        # Store image paths as comma-separated string
        image_paths = ",".join(images)

        # Create new crop entry
        new_crop = Crop(
            name=name,
            description=description,
            growingConditions=growing_conditions,
            harvestTime=harvest_time,
            images=image_paths
        )
        db.session.add(new_crop)
        db.session.commit()

        return {"message": "Crop created successfully.", "crop_id": new_crop.cropId}, 201

    def put(self):
        """Update an entire crop entry."""
        crop_id = request.args.get("crop_id", type=int)
        crop = Crop.query.get(crop_id)
        if not crop:
            return {"message": "Crop not found."}, 404

        data = request.form
        name = data.get("name")
        description = data.get("description")
        growing_conditions = data.get("growingConditions")
        harvest_time = data.get("harvestTime")

        # Validation
        validate_required_field(name, "Crop name")
        validate_min_length(name, "Crop name", 3)
        validate_required_field(description, "Description")

        # Update fields
        crop.name = name
        crop.description = description
        crop.growingConditions = growing_conditions
        crop.harvestTime = harvest_time

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
                    
            crop.images = ",".join(images)  # Replace all images

        db.session.commit()
        return {"message": "Crop updated successfully."}, 200

    def patch(self):
        """Partially update a crop entry."""
        crop_id = request.args.get("crop_id", type=int)
        crop = Crop.query.get(crop_id)
        if not crop:
            return {"message": "Crop not found."}, 404

        data = request.form
        if "name" in data:
            name = data["name"]
            validate_min_length(name, "Crop name", 3)
            crop.name = name

        if "description" in data:
            description = data["description"]
            crop.description = description

        if "growingConditions" in data:
            growing_conditions = data["growingConditions"]
            crop.growingConditions = growing_conditions

        if "harvestTime" in data:
            harvest_time = data["harvestTime"]
            crop.harvestTime = harvest_time

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

            crop.images = ",".join(new_images)

        db.session.commit()
        return {"message": "Crop partially updated successfully."}, 200
    
    def delete(self):
        """Delete a crop entry."""
        crop_id = request.args.get("crop_id", type=int)
        crop = Crop.query.get(crop_id)
        if not crop:
            return {"message": "Crop not found."}, 404
        
        # Delete the crop record from the database
        db.session.delete(crop)
        db.session.commit()
        
        return {"message": "Crop deleted successfully."}, 200