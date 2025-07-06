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

