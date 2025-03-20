from datetime import date
from flask_restful import Resource
from sqlalchemy import func
from models import db, User, Community, Disease, Province, DiagnosisResult, District

class DashboardStatsResource(Resource):
    def get(self):
        """Get stats including disease cases over months and detailed cases per disease."""
        try:
            # Total clients with role 'farmer'
            total_clients = User.query.filter_by(role='farmer').count()

            # Total communities
            total_communities = Community.query.count()

            # Total diseases
            total_diseases = Disease.query.count()
            
            todaysCases = DiagnosisResult.query.filter(
                func.date(DiagnosisResult.date) == date.today()
            ).count()

            # Total cases per province
            provinces = Province.query.all()
            province_cases = []
            for province in provinces:
                total_cases = (
                    db.session.query(DiagnosisResult)
                    .join(District, DiagnosisResult.districtId == District.districtId)
                    .filter(District.provinceId == province.provinceId)
                    .count()
                )
                province_cases.append({
                    "id": province.provinceId,
                    "provinceName": province.name,
                    "totalCases": total_cases
                })

            # Disease cases over months
            cases_over_months = (
                db.session.query(
                    func.to_char(DiagnosisResult.date, 'Month').label('month'),
                    func.date_part('month', DiagnosisResult.date).label('month_number'),
                    func.count(DiagnosisResult.resultId).label('totalCases')
                )
                .group_by(func.to_char(DiagnosisResult.date, 'Month'), func.date_part('month', DiagnosisResult.date))
                .order_by(func.date_part('month', DiagnosisResult.date))
            ).all()

            # Prepare data for chart
            labels = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            month_data = {month.strip(): total_cases for month, _, total_cases in cases_over_months}

            # Fill missing months with 0 cases
            data = [month_data.get(month, 0) for month in labels]

            # Format chart data
            disease_cases_over_months = {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Cases",
                        "data": data,
                        "backgroundColor": "#34d399"
                    }
                ]
            }

            # Number of cases per disease with additional info
            disease_cases = (
                db.session.query(
                    Disease.name.label("diseaseName"),
                    Disease.description.label("description"),
                    Disease.images.label("images"),
                    func.count(DiagnosisResult.resultId).label("totalCases")
                )
                .join(DiagnosisResult, DiagnosisResult.diseaseId == Disease.diseaseId)
                .group_by(Disease.name, Disease.description, Disease.images)
                .all()
            )

            # Format disease cases data
            disease_cases_data = [
                {
                    "diseaseName": disease_name,
                    "description": description,
                    "image": images.split(",")[0] if images else None,  # Get the first image
                    "totalCases": total_cases
                }
                for disease_name, description, images, total_cases in disease_cases
            ]

            # Return the stats in JSON format
            return {
                "totalClients": total_clients,
                "totalCommunities": total_communities,
                "todaysCases": todaysCases,
                "totalDiseases": total_diseases,
                "provinceCases": province_cases,
                "diseaseCasesOverMonths": disease_cases_over_months,
                "diseaseCases": disease_cases_data
            }, 200
        except Exception as e:
            return {"message": f"An error occurred while fetching stats: {str(e)}"}, 500
