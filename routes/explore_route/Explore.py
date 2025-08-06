from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Explore, ExploreType
import cloudinary.uploader

class ExploreListResource(Resource):
    @jwt_required()
    def get(self):
        """List all explore items (optional type filter)"""
        explore_type = request.args.get('type')
        query = Explore.query
        if explore_type:
            query = query.filter_by(type=ExploreType[explore_type.upper()])
        items = query.order_by(Explore.date.desc()).all()
        return {
            "data": [{
                "id": item.id,
                "type": item.type.value,
                "title": item.title,
                "content": item.content,
                "image": item.image,
                "otherImages": item.otherImages,
                "link": item.link,
                "date": item.date.isoformat()
            } for item in items]
        }, 200

    @jwt_required()
    def post(self):
        """Create a new explore item"""
        data = request.form
        required_fields = ['type', 'title', 'content']
        for field in required_fields:
            if field not in data:
                return {"message": f"{field} is required."}, 400
        
        if data['type'] not in ExploreType.__members__:
            return {"message": "Invalid type. Must be UPDATES, ONLINE-SERVICES, or DISEASE-LIBRARY."}, 400

        # Upload image
        image = request.files.get('image')
        if not image:
            return {"message": "Image file is required."}, 400
        
        try:
            image_upload = cloudinary.uploader.upload(image)
            image_url = image_upload.get("url")
        except Exception as e:
            return {"message": f"Image upload failed: {str(e)}"}, 500

        # Optional other images
        other_image_urls = []
        for file in request.files.getlist('otherImages'):
            if file:
                uploaded = cloudinary.uploader.upload(file)
                other_image_urls.append(uploaded.get('url'))
        other_images_string = ",".join(other_image_urls)

        explore_type = ExploreType[data['type'].upper()]
        link = data.get('link')

        new_item = Explore(
            type=explore_type,
            title=data['title'],
            content=data['content'],
            image=image_url,
            otherImages=other_images_string,
            link=link
        )
        db.session.add(new_item)
        db.session.commit()

        return {"message": "Explore item created", "data": new_item.to_dict()}, 201

class ExploreResource(Resource):
    @jwt_required()
    def get(self, exploreId):
        """Get a single explore item by ID"""
        explore = Explore.query.get(exploreId)
        if not explore:
            return {"message": "Explore item not found."}, 404

        data = {
            "id": explore.id,
            "type": explore.type.value,
            "title": explore.title,
            "content": explore.content,
            "image": explore.image,
            "otherImages": explore.otherImages,
            "link": explore.link,
            "date": explore.date.isoformat()
        }

        return {"data": data}, 200

    @jwt_required()
    def put(self, exploreId):
        """Update an explore item"""
        explore = Explore.query.get(exploreId)
        if not explore:
            return {"message": "Explore item not found."}, 404

        data = request.form

        if 'type' in data:
            if data['type'] not in ExploreType.__members__:
                return {"message": "Invalid type. Must be UPDATES, ONLINE-SERVICES, or DISEASE-LIBRARY."}, 400
            explore.type = ExploreType[data['type'].upper()]
        
        explore.title = data.get('title', explore.title)
        explore.content = data.get('content', explore.content)
        explore.link = data.get('link', explore.link)

        if 'image' in request.files:
            try:
                new_image = request.files['image']
                uploaded = cloudinary.uploader.upload(new_image)
                explore.image = uploaded.get('url')
            except Exception as e:
                return {"message": f"Image upload failed: {str(e)}"}, 500

        if 'otherImages' in request.files:
            other_image_urls = []
            for file in request.files.getlist('otherImages'):
                uploaded = cloudinary.uploader.upload(file)
                other_image_urls.append(uploaded.get('url'))
            explore.otherImages = ",".join(other_image_urls)

        db.session.commit()
        return {"message": "Explore item updated successfully."}, 200

    @jwt_required()
    def delete(self, exploreId):
        """Delete an explore item"""
        explore = Explore.query.get(exploreId)
        if not explore:
            return {"message": "Explore item not found."}, 404

        try:
            if explore.image:
                public_id = explore.image.split("/")[-1].split(".")[0]
                cloudinary.uploader.destroy(public_id)

            if explore.otherImages:
                for url in explore.otherImages.split(","):
                    public_id = url.strip().split("/")[-1].split(".")[0]
                    cloudinary.uploader.destroy(public_id)

            db.session.delete(explore)
            db.session.commit()
            return {"message": "Explore item deleted successfully."}, 200

        except Exception as e:
            db.session.rollback()
            return {"message": "Failed to delete explore item.", "error": str(e)}, 500

# import os
# import uuid
# import shutil
# from datetime import datetime
# from flask import request
# from flask_restful import Resource
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from models import db, Explore, ExploreType
# # Keep the import for future reference
# import cloudinary.uploader
# from dotenv import load_dotenv
# import logging

# # Load environment variables
# load_dotenv()
# BACKEND_URL = os.getenv('BACKEND_URL')
# if not BACKEND_URL.endswith('/'):
#     BACKEND_URL += '/'

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Set up storage directories
# UPLOADS_DIR = 'static/uploads/explore'
# if not os.path.exists(UPLOADS_DIR):
#     try:
#         os.makedirs(UPLOADS_DIR)
#     except OSError as e:
#         logger.error(f"Failed to create directory {UPLOADS_DIR}: {str(e)}")

# def save_image_locally(file, subfolder=''):
#     """Save image to local storage and return URL"""
#     if not file:
#         return None
        
#     # Generate unique filename
#     original_filename = file.filename
#     extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
#     unique_filename = f"{uuid.uuid4().hex}.{extension}"
    
#     # Create subfolder if needed
#     target_dir = UPLOADS_DIR
#     if subfolder:
#         target_dir = os.path.join(UPLOADS_DIR, subfolder)
#         if not os.path.exists(target_dir):
#             os.makedirs(target_dir)
    
#     # Save file
#     file_path = os.path.join(target_dir, unique_filename)
#     file.save(file_path)
    
#     # Create URL using BACKEND_URL
#     relative_path = f"static/uploads/explore/{subfolder + '/' if subfolder else ''}{unique_filename}"
#     return f"{BACKEND_URL}{relative_path}"

# def delete_image_locally(image_url):
#     """Delete image from local storage"""
#     if not image_url or not image_url.startswith(BACKEND_URL):
#         return False
    
#     try:
#         # Extract the file path from the URL
#         relative_path = image_url.replace(BACKEND_URL, '')
#         file_path = os.path.join(os.getcwd(), relative_path)
        
#         if os.path.exists(file_path):
#             os.remove(file_path)
#             return True
#     except Exception as e:
#         logger.error(f"Failed to delete image: {str(e)}")
    
#     return False

# class ExploreListResource(Resource):
#     @jwt_required()
#     def get(self):
#         """List all explore items (optional type filter)"""
#         explore_type = request.args.get('type')
#         query = Explore.query
#         if explore_type:
#             query = query.filter_by(type=ExploreType[explore_type.upper()])
#         items = query.order_by(Explore.date.desc()).all()
#         return {
#             "data": [{
#                 "id": item.id,
#                 "type": item.type.value,
#                 "title": item.title,
#                 "content": item.content,
#                 "image": item.image,
#                 "otherImages": item.otherImages,
#                 "link": item.link,
#                 "date": item.date.isoformat()
#             } for item in items]
#         }, 200

#     @jwt_required()
#     def post(self):
#         """Create a new explore item"""
#         data = request.form
#         required_fields = ['type', 'title', 'content']
#         for field in required_fields:
#             if field not in data:
#                 return {"message": f"{field} is required."}, 400
        
#         if data['type'] not in ExploreType.__members__:
#             return {"message": "Invalid type. Must be UPDATES, ONLINE-SERVICES, or DISEASE-LIBRARY."}, 400

#         # Upload main image
#         image = request.files.get('image')
#         if not image:
#             return {"message": "Image file is required."}, 400
        
#         try:
#             # Save image locally
#             type_folder = data['type'].lower()
#             image_url = save_image_locally(image, type_folder)
            
#             # Cloudinary upload code (commented out but preserved)
#             """
#             image_upload = cloudinary.uploader.upload(image)
#             image_url = image_upload.get("url")
#             """
#         except Exception as e:
#             return {"message": f"Image upload failed: {str(e)}"}, 500

#         # Optional other images
#         other_image_urls = []
#         for file in request.files.getlist('otherImages'):
#             if file:
#                 try:
#                     # Save additional images locally
#                     url = save_image_locally(file, type_folder)
#                     other_image_urls.append(url)
                    
#                     # Cloudinary upload code (commented out but preserved)
#                     """
#                     uploaded = cloudinary.uploader.upload(file)
#                     other_image_urls.append(uploaded.get('url'))
#                     """
#                 except Exception as e:
#                     logger.error(f"Failed to upload additional image: {str(e)}")
#                     # Continue with other images
                    
#         other_images_string = ",".join(other_image_urls)

#         explore_type = ExploreType[data['type'].upper()]
#         link = data.get('link')

#         new_item = Explore(
#             type=explore_type,
#             title=data['title'],
#             content=data['content'],
#             image=image_url,
#             otherImages=other_images_string,
#             link=link
#         )
#         db.session.add(new_item)
#         db.session.commit()

#         return {"message": "Explore item created", "data": new_item.to_dict()}, 201

# class ExploreResource(Resource):
#     @jwt_required()
#     def get(self, exploreId):
#         """Get a single explore item by ID"""
#         explore = Explore.query.get(exploreId)
#         if not explore:
#             return {"message": "Explore item not found."}, 404

#         data = {
#             "id": explore.id,
#             "type": explore.type.value,
#             "title": explore.title,
#             "content": explore.content,
#             "image": explore.image,
#             "otherImages": explore.otherImages,
#             "link": explore.link,
#             "date": explore.date.isoformat()
#         }

#         return {"data": data}, 200

#     @jwt_required()
#     def put(self, exploreId):
#         """Update an explore item"""
#         explore = Explore.query.get(exploreId)
#         if not explore:
#             return {"message": "Explore item not found."}, 404

#         data = request.form

#         if 'type' in data:
#             if data['type'] not in ExploreType.__members__:
#                 return {"message": "Invalid type. Must be UPDATES, ONLINE-SERVICES, or DISEASE-LIBRARY."}, 400
#             explore.type = ExploreType[data['type'].upper()]
        
#         explore.title = data.get('title', explore.title)
#         explore.content = data.get('content', explore.content)
#         explore.link = data.get('link', explore.link)

#         type_folder = explore.type.value.lower()
        
#         if 'image' in request.files:
#             try:
#                 new_image = request.files['image']
                
#                 # Delete the old image first
#                 if explore.image:
#                     delete_image_locally(explore.image)
                    
#                 # Save the new image
#                 explore.image = save_image_locally(new_image, type_folder)
                
#                 # Cloudinary upload code (commented out but preserved)
#                 """
#                 uploaded = cloudinary.uploader.upload(new_image)
#                 explore.image = uploaded.get('url')
#                 """
#             except Exception as e:
#                 return {"message": f"Image upload failed: {str(e)}"}, 500

#         if 'otherImages' in request.files:
#             # Delete old other images
#             if explore.otherImages:
#                 for url in explore.otherImages.split(","):
#                     delete_image_locally(url)
            
#             # Upload new other images
#             other_image_urls = []
#             for file in request.files.getlist('otherImages'):
#                 try:
#                     # Save additional images locally
#                     url = save_image_locally(file, type_folder)
#                     other_image_urls.append(url)
                    
#                     # Cloudinary upload code (commented out but preserved)
#                     """
#                     uploaded = cloudinary.uploader.upload(file)
#                     other_image_urls.append(uploaded.get('url'))
#                     """
#                 except Exception as e:
#                     logger.error(f"Failed to upload additional image: {str(e)}")
#                     # Continue with other images
                    
#             explore.otherImages = ",".join(other_image_urls)

#         db.session.commit()
#         return {"message": "Explore item updated successfully."}, 200

#     @jwt_required()
#     def delete(self, exploreId):
#         """Delete an explore item"""
#         explore = Explore.query.get(exploreId)
#         if not explore:
#             return {"message": "Explore item not found."}, 404

#         try:
#             # Delete main image
#             if explore.image:
#                 delete_image_locally(explore.image)
                
#                 # Cloudinary deletion code (commented out but preserved)
#                 """
#                 public_id = explore.image.split("/")[-1].split(".")[0]
#                 cloudinary.uploader.destroy(public_id)
#                 """

#             # Delete other images
#             if explore.otherImages:
#                 for url in explore.otherImages.split(","):
#                     delete_image_locally(url)
                    
#                     # Cloudinary deletion code (commented out but preserved)
#                     """
#                     public_id = url.strip().split("/")[-1].split(".")[0]
#                     cloudinary.uploader.destroy(public_id)
#                     """

#             db.session.delete(explore)
#             db.session.commit()
#             return {"message": "Explore item deleted successfully."}, 200

#         except Exception as e:
#             db.session.rollback()
#             return {"message": "Failed to delete explore item.", "error": str(e)}, 500