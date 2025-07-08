from flask import request, send_file, current_app
from flask_restful import Resource, abort
from models import db, ModelVersion, ModelRating
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
import hashlib, os



def is_admin():
    claims = get_jwt_identity()
    return claims.get('role') == 'admin'

class LatestModelResource(Resource):
    @jwt_required()
    def get(self):
        
        model = ModelVersion.query.filter_by(isActive=True).order_by(ModelVersion.releaseDate.desc()).first()
        if not model:
            abort(404, message="No active model found.")
        return {"model": model.to_dict()}, 200


class DownloadModelResource(Resource):
    @jwt_required()
    def get(self, model_id):
        
        model = ModelVersion.query.get_or_404(model_id)
        file_path = os.path.join(current_app.config['MODEL_STORAGE'], model.filePath)
        if not os.path.exists(file_path):
            abort(404, message="Model file not found.")

        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"plant_disease_model_v{model.version}.tflite"
        )

class DownloadModelConfigResource(Resource):
    def get(self, model_id):
        """Download the configuration (classes.json) file for a specific model version"""
        model = ModelVersion.query.get(model_id)
        if not model:
            abort(404, message="Model not found.")

        config_path = os.path.join(current_app.config['MODEL_STORAGE'], model.configPath)

        if not os.path.exists(config_path):
            abort(404, message="Configuration file not found.")

        return send_file(
            config_path,
            as_attachment=True,
            download_name=f"plant_disease_classes_v{model.version}.json"
        )


class RateModelResource(Resource):
    @jwt_required()
    def post(self, model_id):
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])
        
        model = ModelVersion.query.get_or_404(model_id)
        data = request.json

        new_rating = ModelRating(
            modelId=model_id,
            userId=userId,
            offlineId=data.get('offlineId'),
            rating=data.get('rating'),
            feedback=data.get('feedback'),
            diagnosisResult=data.get('diagnosisResult'),
            diagnosisCorrect=data.get('diagnosisCorrect'),
            cropType=data.get('cropType'),
            deviceInfo=data.get('deviceInfo')
        )
        
        try:
            db.session.add(new_rating)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"message": "An error occurred", "error": str(e)}, 500

        return {"message": "Rating submitted successfully.", "data": new_rating.to_dict()}, 201


class SyncOfflineRatingsResource(Resource):
    @jwt_required()
    def post(self):
        
        user_identity = get_jwt_identity()
        userId = int(user_identity["userId"])
        
        data = request.json
        successful_ids = []
        new_ratings = []

        for rating_data in data.get('ratings', []):
            existing = ModelRating.query.filter_by(offlineId=rating_data.get('offlineId')).first()
            model = ModelVersion.query.get_or_404(rating_data.get('modelId'))
            if existing:
                successful_ids.append(rating_data.get('offlineId'))
                continue

            try:
                new_rating = ModelRating(
                    modelId=rating_data.get('modelId'),
                    userId=userId,
                    offlineId=rating_data.get('offlineId'),
                    rating=rating_data.get('rating'),
                    feedback=rating_data.get('feedback'),
                    diagnosisResult=rating_data.get('diagnosisResult'),
                    diagnosisCorrect=rating_data.get('diagnosisCorrect'),
                    cropType=rating_data.get('cropType'),
                    deviceInfo=rating_data.get('deviceInfo'),
                    createdAt=datetime.fromisoformat(rating_data.get('createdAt', datetime.utcnow().isoformat()))
                )
                db.session.add(new_rating)
                new_ratings.append(new_rating)
                successful_ids.append(rating_data.get('offlineId'))
            except Exception as e:
                current_app.logger.error(f"Error syncing rating: {str(e)}")

        try:   
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"message": "An error occurred", "error": str(e)}, 500
        
        return {"success": True, "syncedIds": successful_ids, "data": [new_rating.to_dict() for new_rating in new_ratings]}, 200


class AdminModelResource(Resource):
    
    @jwt_required()
    def get(self):
        if not is_admin():
            return {"message": "Admins only: You are not authorized to access this resource."}, 403
        
        models = ModelVersion.query.order_by(ModelVersion.releaseDate.desc()).all()

        result = []
        for model in models:
            ratings = ModelRating.query.filter_by(modelId=model.modelId).all()
            result.append({
                "model": model.to_dict(),
                "ratings": [r.to_dict() for r in ratings]
            })

        return {"data": result}, 200
    
    @jwt_required()
    def post(self):
        """Create a new model version (with .tflite + classes.json)"""
        if not is_admin():
            return {"message": "Admins only: You are not authorized to perform this action."}, 403
        
        data = request.form
        model_file = request.files.get('model_file')
        config_file = request.files.get('config_file')

        if not model_file:
            abort(400, message="No model file provided.")
        if not config_file:
            abort(400, message="No configuration file provided.")

        version = data.get('version')
        if not version:
            abort(400, message="Model version is required.")

        # Generate file names and paths
        model_filename = f"plant_disease_model_v{version}.tflite"
        config_filename = f"plant_disease_classes_v{version}.json"
        model_path = os.path.join(current_app.config['MODEL_STORAGE'], model_filename)
        config_path = os.path.join(current_app.config['MODEL_STORAGE'], config_filename)

        # Save files
        model_file.save(model_path)
        config_file.save(config_path)

        # Calculate file sizes and hashes
        try:
            model_size = os.path.getsize(model_path) // 1024
            model_hash = hashlib.sha256(open(model_path, 'rb').read()).hexdigest()

            config_size = os.path.getsize(config_path) // 1024
            config_hash = hashlib.sha256(open(config_path, 'rb').read()).hexdigest()
        except Exception as e:
            # Clean up on error
            if os.path.exists(model_path): os.remove(model_path)
            if os.path.exists(config_path): os.remove(config_path)
            abort(500, message=f"Failed to process files: {str(e)}")


        # Save model record
        new_model = ModelVersion(
            version=version,
            fileSize=model_size,
            fileHash=model_hash,
            filePath=model_filename,
            configSize=config_size,
            configHash=config_hash,
            configPath=config_filename,
            accuracy=data.get('accuracy'),
            isActive=data.get('isActive', True)
        )

        try:
            db.session.add(new_model)
            db.session.commit()
        
        except Exception as e:
            db.session.rollback()
            return {"message": "An error occurred", "error": str(e)}, 500

        return {
            "message": "Model created successfully",
            "model": new_model.to_dict()
        }, 201
        
        
