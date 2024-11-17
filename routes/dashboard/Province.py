from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required
from models import db, Province

class ProvinceResource(Resource):

    @jwt_required()
    def get(self):
        """Fetch all provinces with their districts."""
        try:
            # Fetch all provinces and their districts
            provinces = Province.query.options(db.joinedload(Province.districts)).all()

            # Prepare the response data
            province_data = [
                {
                    "id": province.provinceId,
                    "name": province.name,
                    "districts": [
                        {"id": district.districtId, "name": district.name}
                        for district in province.districts
                    ]
                }
                for province in provinces
            ]

            return {"data": province_data}, 200

        except Exception as e:
            abort(500, message="An error occurred while fetching provinces: " + str(e))
