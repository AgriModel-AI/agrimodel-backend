from datetime import datetime
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required
from flask_restful import Resource, abort
from models import db, DiagnosisResult, Disease, District, User
import cloudinary.uploader


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Utility function to check if a file is an allowed image type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class DiagnosisResultResource(Resource):
    
    @jwt_required()
    def get(self, result_id=None):
        """Retrieve diagnosis results or a specific result."""
        if result_id:
            result = DiagnosisResult.query.get(result_id)
            if not result:
                return {"message": "Diagnosis result not found."}, 404

            # Serialize result
            return jsonify({
                "resultId": result.resultId,
                "user": {
                    "id": result.userId,
                    "username": result.user.username if result.user else None,
                    "email": result.user.email if result.user else None,
                    "phone_number": result.user.phone_number if result.user else None,
                },
                "disease": {
                    "id": result.disease.diseaseId if result.disease else None,
                    "name": result.disease.name if result.disease else None,
                },
                "district": {
                    "provinceName": result.district.province.name if result.district and result.district.province else None,
                    "districtName": result.district.name if result.district else None,
                },
                "date": result.date.isoformat(),
                "image_path": result.image_path,
                "detected": result.detected
            })

        else:
            results = DiagnosisResult.query.all()
            return jsonify({
                "data": [self.serialize_result(result) for result in results]
            })

    def serialize_result(self, result):
        """Helper method to serialize a DiagnosisResult."""
        return {
            "resultId": result.resultId,
            "user": {
                "id": result.userId,
                "username": result.user.username if result.user else None,
                "email": result.user.email if result.user else None,
                "phone_number": result.user.phone_number if result.user else None,
            },
            "disease": {
                "id": result.disease.diseaseId if result.disease else None,
                "name": result.disease.name if result.disease else None,
            },
            "district": {
                "provinceName": result.district.province.name if result.district and result.district.province else None,
                "districtName": result.district.name if result.district else None,
            },
            "date": result.date.isoformat(),
            "image_path": result.image_path,
            "detected": result.detected
        }

    @jwt_required()
    def post(self):
        """Create a new diagnosis result."""
        data = request.form
        user_id = data.get("userId")
        disease_id = data.get("diseaseId")
        district_id = data.get("districtId")
        detected = data.get("detected", type=bool, default=False)

        # Validate required fields
        if not user_id:
            abort(400, message="User ID is required.")

        # Validate if user exists
        user = User.query.get(user_id)
        if not user:
            abort(404, message="User not found.")

        if not district_id:
            abort(400, message="District ID is required.")

        # Validate if district exists
        district = District.query.get(district_id)
        if not district:
            abort(404, message="District not found.")

        # Validate if disease exists (optional)
        disease = None
        if disease_id:
            disease = Disease.query.get(disease_id)
            if not disease:
                abort(404, message="Disease not found.")

        # Validate if image is provided
        image = request.files.get("image")
        if not image:
            abort(400, message="Image is required.")

        # Validate image format
        if not allowed_file(image.filename):
            abort(400, message="Invalid image format. Allowed: png, jpg, jpeg, gif.")

        try:
            # Upload the file to Cloudinary
            upload_result = cloudinary.uploader.upload(image)

            # Get the URL of the uploaded image
            image_url = upload_result.get('url')
        except Exception as e:
            return {"message": f"Image upload failed: {str(e)}"}, 404
        
        # Create a new diagnosis result
        new_result = DiagnosisResult(
            userId=user_id,
            diseaseId=disease_id,
            districtId=district_id,
            date=datetime.utcnow(),
            image_path=image_url,
            detected=detected
        )

        try:
            db.session.add(new_result)
            db.session.commit()
            return {"message": "Diagnosis result created successfully.", "resultId": new_result.resultId}, 201
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"An error occurred while saving the diagnosis result: {str(e)}")
