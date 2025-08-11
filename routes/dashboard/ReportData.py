from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, abort
from models import db, DiagnosisResult, Disease, Crop, User, District, Province, ModelVersion, ModelRating
from models import Community, UserCommunity, Post, SupportRequest
from sqlalchemy import func, desc, case, extract, and_, text
from datetime import datetime, timedelta

class ReportDataResource(Resource):
    """Resource that returns only JSON data for report generation on the frontend"""
    
    @jwt_required()
    def get(self, report_type=None):
        """Return structured JSON data for frontend report generation"""
        # Verify user has permissions to access reports
        user_identity = get_jwt_identity()
        user_id = int(user_identity["userId"])
        user = User.query.get(user_id)
        
        if not user or user.role not in ['admin', 'researcher', 'manager']:
            return {"message": "You don't have permission to access reports."}, 403
        
        # Get date range parameters
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = datetime.now() - timedelta(days=30)  # Default to last 30 days
                
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date = datetime.now()
                
            # Ensure end_date is at the end of the day
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
        except ValueError:
            return {"message": "Invalid date format. Use YYYY-MM-DD."}, 400
        
        # Check if report type is specified
        if not report_type:
            return {"message": "Report type is required."}, 400
        
        # Generate the appropriate data based on report type
        if report_type == 'disease_prevalence':
            return self.get_disease_prevalence_data(start_date, end_date)
        elif report_type == 'model_performance':
            return self.get_model_performance_data(start_date, end_date)
        elif report_type == 'user_engagement':
            return self.get_user_engagement_data(start_date, end_date)
        elif report_type == 'regional_insights':
            return self.get_regional_insights_data(start_date, end_date)
        elif report_type == 'support_analysis':
            return self.get_support_analysis_data(start_date, end_date)
        elif report_type == 'economic_impact':
            return self.get_economic_impact_data(start_date, end_date)
        elif report_type == 'client_activity':
            return self.get_client_activity_data(start_date, end_date)
        elif report_type == 'growth_analysis':
            return self.get_growth_analysis_data(start_date, end_date)
        else:
            return {"message": f"Unknown report type: {report_type}"}, 400
    
    def get_disease_prevalence_data(self, start_date, end_date):
        """Return disease prevalence data for the given date range"""
        # Query: Disease detection frequency by crop
        disease_by_crop = db.session.query(
            Crop.name.label('crop_name'),
            Disease.name.label('disease_name'),
            func.count(DiagnosisResult.resultId).label('detection_count')
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).join(
            Crop, Disease.cropId == Crop.cropId
        ).filter(
            DiagnosisResult.detected == True,
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            Crop.name, Disease.name
        ).order_by(
            desc('detection_count')
        ).all()
        
        # Query: Geographic hotspots
        geographic_hotspots = db.session.query(
            Province.name.label('province'),
            District.name.label('district'),
            Disease.name.label('disease'),
            func.count(DiagnosisResult.resultId).label('cases')
        ).join(
            District, DiagnosisResult.districtId == District.districtId
        ).join(
            Province, District.provinceId == Province.provinceId
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).filter(
            DiagnosisResult.detected == True,
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            Province.name, District.name, Disease.name
        ).order_by(
            desc('cases')
        ).all()
        
        # Query: Disease trends over time (by month)
        disease_trends = db.session.query(
            func.date_trunc('month', DiagnosisResult.date).label('month'),
            Disease.name.label('disease_name'),
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).filter(
            DiagnosisResult.detected == True,
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            'month', Disease.name
        ).order_by(
            'month'
        ).all()
        
        # Format data for JSON response
        disease_by_crop_data = [
            {"crop": item[0], "disease": item[1], "count": item[2]} 
            for item in disease_by_crop
        ]
        
        geographic_data = [
            {"province": item[0], "district": item[1], "disease": item[2], "cases": item[3]} 
            for item in geographic_hotspots
        ]
        
        trend_data = [
            {"month": item[0].strftime('%Y-%m'), "disease": item[1], "count": item[2]} 
            for item in disease_trends
        ]
        
        # Calculate summary statistics
        total_diagnoses = sum(item[2] for item in disease_by_crop)
        unique_crops = len(set(item[0] for item in disease_by_crop))
        unique_diseases = len(set(item[1] for item in disease_by_crop))
        
        # Find top disease and crop
        top_disease = max([(item[1], item[2]) for item in disease_by_crop], key=lambda x: x[1])[0] if disease_by_crop else "None"
        
        # Aggregate by crop
        crop_counts = {}
        for item in disease_by_crop:
            crop = item[0]
            count = item[2]
            crop_counts[crop] = crop_counts.get(crop, 0) + count
        
        top_crop = max(crop_counts.items(), key=lambda x: x[1])[0] if crop_counts else "None"
        
        # Prepare chart data
        # Top 5 diseases
        disease_counts = {}
        for item in disease_by_crop:
            disease = item[1]
            count = item[2]
            disease_counts[disease] = disease_counts.get(disease, 0) + count
        
        top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_diseases_data = [{"disease": k, "count": v} for k, v in top_diseases]
        
        # Regional distribution
        province_counts = {}
        for item in geographic_hotspots:
            province = item[0]
            count = item[3]
            province_counts[province] = province_counts.get(province, 0) + count
        
        region_data = [{"province": k, "cases": v} for k, v in province_counts.items()]
        
        return jsonify({
            "title": "Monthly Disease Surveillance Report",
            "dateRange": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "summary": {
                "totalDiagnoses": total_diagnoses,
                "uniqueCrops": unique_crops,
                "uniqueDiseases": unique_diseases,
                "topDisease": top_disease,
                "topCrop": top_crop
            },
            "tables": {
                "diseaseByCrop": disease_by_crop_data,
                "geographicHotspots": geographic_data,
                "diseaseTrends": trend_data
            },
            "chartData": {
                "topDiseases": top_diseases_data,
                "regionalDistribution": region_data,
                "trendData": trend_data
            }
        })
    
    def get_model_performance_data(self, start_date, end_date):
        """Return model performance data for the given date range"""
        # Query model performance data
        model_data = db.session.query(
            ModelVersion.version,
            func.avg(ModelRating.rating).label('avg_rating'),
            func.sum(case((ModelRating.diagnosisCorrect == True, 1), else_=0)).label('correct_diagnoses'),
            func.count(ModelRating.ratingId).label('total_ratings'),
            ModelVersion.releaseDate
        ).outerjoin(
            ModelRating, 
            and_(
                ModelVersion.modelId == ModelRating.modelId,
                ModelRating.createdAt.between(start_date, end_date)
            )
        ).filter(
            ModelVersion.releaseDate <= end_date
        ).group_by(
            ModelVersion.version, ModelVersion.releaseDate
        ).order_by(
            desc(ModelVersion.releaseDate)
        ).all()
        
        # Performance by disease type - FIXED QUERY
        disease_performance = db.session.query(
            Disease.name.label('disease_name'),
            func.count(DiagnosisResult.resultId).label('total_diagnoses'),
            func.sum(case((DiagnosisResult.detected == True, 1), else_=0)).label('positive_diagnoses'),
            func.avg(ModelRating.rating).label('avg_rating')  # Added missing avg rating
        ).join(
            DiagnosisResult, Disease.diseaseId == DiagnosisResult.diseaseId
        ).outerjoin(
            ModelRating, 
            and_(
                ModelRating.modelId.in_(
                    db.session.query(ModelVersion.modelId).filter(
                        ModelVersion.isActive == True
                    )
                ),
                ModelRating.createdAt.between(start_date, end_date)
            )
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            Disease.name
        ).having(
            func.count(DiagnosisResult.resultId) > 0
        ).order_by(
            desc('total_diagnoses')
        ).all()
        
        # Format data for JSON response
        model_performance_data = []
        for item in model_data:
            accuracy = (item[2] / item[3] * 100) if item[3] > 0 else 0
            model_performance_data.append({
                "version": item[0],
                "avgRating": round(item[1] or 0, 2),
                "correctDiagnoses": item[2],
                "totalRatings": item[3],
                "accuracy": round(accuracy, 2),
                "releaseDate": item[4].strftime('%Y-%m-%d') if item[4] else None
            })
        
        # FIXED: Disease performance data formatting
        disease_performance_data = []
        for item in disease_performance:
            detection_accuracy = (item[2] / item[1] * 100) if item[1] > 0 else 0  # positive/total diagnoses
            disease_performance_data.append({
                "disease": item[0],
                "avgRating": round(item[3] or 0, 2),  # Now correctly accessing avg_rating (item[3])
                "totalDiagnoses": item[1],           # total_diagnoses
                "positiveDiagnoses": item[2],        # positive_diagnoses  
                "detectionAccuracy": round(detection_accuracy, 2)  # More meaningful than "accuracy"
            })
        
        # Calculate summary metrics - FIXED
        overall_accuracy = sum(item["accuracy"] for item in model_performance_data) / len(model_performance_data) if model_performance_data else 0
        best_model = max(model_performance_data, key=lambda x: x["accuracy"])["version"] if model_performance_data else "None"
        total_ratings = sum(item["totalRatings"] for item in model_performance_data)
                
        return jsonify({
            "title": "Quarterly AI Model Performance Assessment",
            "dateRange": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "summary": {
                "overallAccuracy": round(overall_accuracy, 2),
                "bestModel": best_model,
                "totalRatings": total_ratings
            },
            "tables": {
                "modelPerformance": model_performance_data,
                "diseasePerformance": disease_performance_data
            },
            "chartData": {
                "accuracyByVersion": [
                    {"version": item["version"], "accuracy": item["accuracy"]} 
                    for item in model_performance_data
                ],
                "diseaseDetectionAccuracy": [
                    {"disease": item["disease"], "accuracy": item["detectionAccuracy"]} 
                    for item in disease_performance_data
                ]
            }
        })
    
    def get_user_engagement_data(self, start_date, end_date):
        """Return user engagement data for the given date range"""
        # Query: Active users by diagnosis activity
        active_users = db.session.query(
            User.userId,
            User.username,
            func.count(DiagnosisResult.resultId).label('diagnosis_count'),
            func.max(DiagnosisResult.date).label('last_diagnosis')
        ).join(
            DiagnosisResult, User.userId == DiagnosisResult.userId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            User.userId, User.username
        ).order_by(
            desc('diagnosis_count')
        ).all()
        
        # Query: Community participation metrics
        community_metrics = db.session.query(
            Community.name.label('community_name'),
            func.count(func.distinct(UserCommunity.userId)).label('member_count'),
            func.count(Post.postId).label('post_count'),
            func.count(func.distinct(Post.userId)).label('active_posters')
        ).outerjoin(
            UserCommunity, Community.communityId == UserCommunity.communityId
        ).outerjoin(
            Post, and_(
                Community.communityId == Post.communityId,
                Post.createdAt.between(start_date, end_date)
            )
        ).group_by(
            Community.name
        ).order_by(
            desc('member_count')
        ).all()
        
        # Query: User activity trends over time
        user_trends = db.session.query(
            func.date_trunc('day', DiagnosisResult.date).label('date'),
            func.count(func.distinct(DiagnosisResult.userId)).label('active_users'),
            func.count(DiagnosisResult.resultId).label('diagnoses')
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            'date'
        ).order_by(
            'date'
        ).all()
        
        # Format data for JSON response
        user_data = []
        for item in active_users:
            user_data.append({
                "userId": item[0],
                "username": item[1],
                "diagnosisCount": item[2],
                "lastDiagnosis": item[3].strftime('%Y-%m-%d') if item[3] else None
            })
        
        community_data = []
        for item in community_metrics:
            community_data.append({
                "community": item[0],
                "members": item[1],
                "posts": item[2],
                "activePosters": item[3]
            })
        
        trend_data = []
        for item in user_trends:
            trend_data.append({
                "date": item[0].strftime('%Y-%m-%d'),
                "activeUsers": item[1],
                "diagnoses": item[2]
            })
        
        # Calculate summary statistics
        total_active_users = len(user_data)
        total_diagnoses = sum(item["diagnosisCount"] for item in user_data)
        avg_diagnoses_per_user = round(total_diagnoses / total_active_users, 2) if total_active_users > 0 else 0
        most_active_user = user_data[0]["username"] if user_data else "None"
        most_active_community = community_data[0]["community"] if community_data else "None"
        
        return jsonify({
            "title": "User Engagement Analytics Report",
            "dateRange": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "summary": {
                "totalActiveUsers": total_active_users,
                "totalDiagnoses": total_diagnoses,
                "avgDiagnosesPerUser": avg_diagnoses_per_user,
                "mostActiveUser": most_active_user,
                "mostActiveCommity": most_active_community
            },
            "tables": {
                "activeUsers": user_data,
                "communityMetrics": community_data,
                "activityTrends": trend_data
            },
            "chartData": {
                "userActivity": trend_data,
                "topUsers": sorted(user_data, key=lambda x: x["diagnosisCount"], reverse=True)[:10],
                "communityEngagement": sorted(community_data, key=lambda x: x["posts"], reverse=True)
            }
        })
    
    def get_regional_insights_data(self, start_date, end_date):
        """Return regional insights data for the given date range"""
        # Query: Crop disease prevalence by region
        regional_data = db.session.query(
            Province.name.label('province'),
            Crop.name.label('crop'),
            Disease.name.label('disease'),
            func.count(DiagnosisResult.resultId).label('occurrences')
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).join(
            Crop, Disease.cropId == Crop.cropId
        ).join(
            District, DiagnosisResult.districtId == District.districtId
        ).join(
            Province, District.provinceId == Province.provinceId
        ).filter(
            DiagnosisResult.detected == True,
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            Province.name, Crop.name, Disease.name
        ).order_by(
            Province.name, desc('occurrences')
        ).all()
        
        # Query: District-level analysis
        district_data = db.session.query(
            Province.name.label('province'),
            District.name.label('district'),
            func.count(DiagnosisResult.resultId).label('total_cases'),
            func.count(func.distinct(Disease.diseaseId)).label('unique_diseases')
        ).join(
            District, DiagnosisResult.districtId == District.districtId
        ).join(
            Province, District.provinceId == Province.provinceId
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).filter(
            DiagnosisResult.detected == True,
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            Province.name, District.name
        ).order_by(
            desc('total_cases')
        ).all()
        
        # Format data for JSON response
        region_disease_data = []
        for item in regional_data:
            region_disease_data.append({
                "province": item[0],
                "crop": item[1],
                "disease": item[2],
                "occurrences": item[3]
            })
        
        district_analysis_data = []
        for item in district_data:
            district_analysis_data.append({
                "province": item[0],
                "district": item[1],
                "totalCases": item[2],
                "uniqueDiseases": item[3]
            })
        
        # Calculate regional summary statistics
        provinces_count = len(set(item[0] for item in regional_data))
        total_cases = sum(item[3] for item in regional_data)
        
        # Find most affected province and district
        province_cases = {}
        for item in district_data:
            province = item[0]
            cases = item[2]
            province_cases[province] = province_cases.get(province, 0) + cases
        
        most_affected_province = max(province_cases.items(), key=lambda x: x[1])[0] if province_cases else "None"
        most_affected_district = district_data[0][1] if district_data else "None"
        
        # Find most affected crop
        crop_cases = {}
        for item in regional_data:
            crop = item[1]
            cases = item[3]
            crop_cases[crop] = crop_cases.get(crop, 0) + cases
        
        most_affected_crop = max(crop_cases.items(), key=lambda x: x[1])[0] if crop_cases else "None"
        
        # Create province summary for charts
        province_summary = []
        for province, cases in province_cases.items():
            province_summary.append({
                "province": province,
                "cases": cases
            })
        
        province_summary.sort(key=lambda x: x["cases"], reverse=True)
        
        # Create crop by region summary
        crop_by_region = []
        for province in set(item[0] for item in regional_data):
            for crop in set(item[1] for item in regional_data if item[0] == province):
                total = sum(item[3] for item in regional_data if item[0] == province and item[1] == crop)
                crop_by_region.append({
                    "province": province,
                    "crop": crop,
                    "occurrences": total
                })
        
        crop_by_region.sort(key=lambda x: (x["province"], -x["occurrences"]))
        
        return jsonify({
            "title": "Regional Agricultural Risk Report",
            "dateRange": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "summary": {
                "provincesCount": provinces_count,
                "totalCases": total_cases,
                "mostAffectedProvince": most_affected_province,
                "mostAffectedDistrict": most_affected_district,
                "mostAffectedCrop": most_affected_crop
            },
            "tables": {
                "regionalData": region_disease_data,
                "districtData": district_analysis_data,
                "provinceSummary": province_summary,
                "cropByRegion": crop_by_region
            },
            "chartData": {
                "provinceCases": province_summary,
                "topDistricts": sorted(district_analysis_data, key=lambda x: x["totalCases"], reverse=True)[:10],
                "cropDistribution": sorted(crop_by_region, key=lambda x: x["occurrences"], reverse=True)[:15]
            }
        })
    
    def get_support_analysis_data(self, start_date, end_date):
        """Return support system analysis data for the given date range"""
        # Query: Support requests by type and resolution time
        support_data = db.session.query(
            SupportRequest.type,
            func.count(SupportRequest.requestId).label('request_count'),
            func.avg(extract('epoch', SupportRequest.updatedAt - SupportRequest.createdAt)/3600).label('avg_resolution_hours')
        ).filter(
            SupportRequest.status == 'RESOLVED',
            SupportRequest.createdAt.between(start_date, end_date)
        ).group_by(
            SupportRequest.type
        ).order_by(
            desc('request_count')
        ).all()
        
        # Query: Support requests by status
        status_data = db.session.query(
            SupportRequest.status,
            func.count(SupportRequest.requestId).label('count')
        ).filter(
            SupportRequest.createdAt.between(start_date, end_date)
        ).group_by(
            SupportRequest.status
        ).order_by(
            desc('count')
        ).all()
        
        # Query: Support requests trend over time
        trend_data = db.session.query(
            func.date_trunc('day', SupportRequest.createdAt).label('date'),
            func.count(SupportRequest.requestId).label('request_count')
        ).filter(
            SupportRequest.createdAt.between(start_date, end_date)
        ).group_by(
            'date'
        ).order_by(
            'date'
        ).all()
        
        # Format data for JSON response
        support_type_data = []
        for item in support_data:
            support_type_data.append({
                "type": str(item[0].value) if hasattr(item[0], 'value') else str(item[0]),
                "count": item[1],
                "avgResolutionHours": round(item[2] or 0, 2)
            })
        
        status_count_data = []
        for item in status_data:
            status_count_data.append({
                "status": str(item[0].value) if hasattr(item[0], 'value') else str(item[0]),
                "count": item[1]
            })
        
        request_trend_data = []
        for item in trend_data:
            request_trend_data.append({
                "date": item[0].strftime('%Y-%m-%d'),
                "count": item[1]
            })
        
        # Calculate summary statistics
        total_requests = sum(item["count"] for item in support_type_data)
        avg_resolution_time = sum(item["avgResolutionHours"] * item["count"] for item in support_type_data) / total_requests if total_requests > 0 else 0
        most_common_type = support_type_data[0]["type"] if support_type_data else "None"
        
        # Get pending requests count
        pending_requests = next((item["count"] for item in status_count_data if item["status"] == "PENDING"), 0)
        
        # Calculate resolution rate
        resolved_count = next((item["count"] for item in status_count_data if item["status"] == "RESOLVED"), 0)
        resolution_rate = (resolved_count / total_requests * 100) if total_requests > 0 else 0
        
        return jsonify({
            "title": "Support System Analysis Report",
            "dateRange": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "summary": {
                "totalRequests": total_requests,
                "avgResolutionTime": round(avg_resolution_time, 2),
                "mostCommonType": most_common_type,
                "pendingRequests": pending_requests,
                "resolutionRate": round(resolution_rate, 2)
            },
            "tables": {
                "requestsByType": support_type_data,
                "requestsByStatus": status_count_data,
                "requestTrends": request_trend_data
            },
            "chartData": {
                "requestTypeDistribution": support_type_data,
                "statusDistribution": status_count_data,
                "dailyRequestVolume": request_trend_data
            }
        })
    
    def get_economic_impact_data(self, start_date, end_date):
        """Return economic impact assessment data for the given date range"""
        # Query diagnosis results for economic calculations
        diagnosis_data = db.session.query(
            Crop.name.label('crop_name'),
            Disease.name.label('disease_name'),
            func.count(DiagnosisResult.resultId).label('detection_count'),
            Province.name.label('province')
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).join(
            Crop, Disease.cropId == Crop.cropId
        ).join(
            District, DiagnosisResult.districtId == District.districtId
        ).join(
            Province, District.provinceId == Province.provinceId
        ).filter(
            DiagnosisResult.detected == True,
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            Crop.name, Disease.name, Province.name
        ).all()
        
        # Mock economic data - in a real system these would come from database or calculations
        avg_yield_per_hectare = {
            'Rice': 4.5,  # tons per hectare
            'Maize': 5.2,
            'Wheat': 3.8,
            'Potato': 25.0,
            'Tomato': 35.0,
            'Coffee': 0.9,
            'Tea': 2.1,
            'Cassava': 15.0,
            'Default': 5.0  # Default value for crops not in the list
        }
        
        avg_price_per_ton = {
            'Rice': 380,  # dollars per ton
            'Maize': 175,
            'Wheat': 210,
            'Potato': 300,
            'Tomato': 750,
            'Coffee': 2500,
            'Tea': 2700,
            'Cassava': 150,
            'Default': 500  # Default value for crops not in the list
        }
        
        avg_loss_percentage = {
            'Blast Disease': 30,  # percent yield loss
            'Leaf Rust': 25,
            'Powdery Mildew': 20,
            'Late Blight': 40,
            'Bacterial Wilt': 35,
            'Anthracnose': 15,
            'Fusarium Wilt': 30,
            'Default': 25  # Default value for diseases not in the list
        }
        
        # Assumed average farm size in hectares
        avg_farm_size = 2.5
        
        # Calculate economic impact
        economic_data = []
        for item in diagnosis_data:
            crop = item[0]
            disease = item[1]
            detections = item[2]
            province = item[3]
            
            yield_per_hectare = avg_yield_per_hectare.get(crop, avg_yield_per_hectare['Default'])
            price_per_ton = avg_price_per_ton.get(crop, avg_price_per_ton['Default'])
            loss_percentage = avg_loss_percentage.get(disease, avg_loss_percentage['Default'])
            
            potential_loss = yield_per_hectare * price_per_ton * (loss_percentage/100) * avg_farm_size
            estimated_savings = potential_loss * 0.7 * detections  # Assuming early detection saves 70% of potential loss
            
            economic_data.append({
                "crop": crop,
                "disease": disease,
                "province": province,
                "detections": detections,
                "yieldPerHectare": yield_per_hectare,
                "pricePerTon": price_per_ton,
                "lossPercentage": loss_percentage,
                "potentialLoss": round(potential_loss, 2),
                "estimatedSavings": round(estimated_savings, 2)
            })
        
        # Calculate crop summary
        crop_summary = {}
        for item in economic_data:
            crop = item["crop"]
            if crop not in crop_summary:
                crop_summary[crop] = {"detections": 0, "savings": 0}
            
            crop_summary[crop]["detections"] += item["detections"]
            crop_summary[crop]["savings"] += item["estimatedSavings"]
        
        crop_summary_data = [
            {"crop": crop, "detections": data["detections"], "savings": round(data["savings"], 2)}
            for crop, data in crop_summary.items()
        ]
        
        # Calculate province summary
        province_summary = {}
        for item in economic_data:
            province = item["province"]
            if province not in province_summary:
                province_summary[province] = {"detections": 0, "savings": 0}
            
            province_summary[province]["detections"] += item["detections"]
            province_summary[province]["savings"] += item["estimatedSavings"]
        
        province_summary_data = [
            {"province": province, "detections": data["detections"], "savings": round(data["savings"], 2)}
            for province, data in province_summary.items()
        ]
        
        # Calculate totals
        total_detections = sum(item["detections"] for item in economic_data)
        total_potential_loss = sum(item["potentialLoss"] * item["detections"] for item in economic_data)
        total_estimated_savings = sum(item["estimatedSavings"] for item in economic_data)
        
        # Calculate ROI (assuming system cost of $25,000)
        system_cost = 25000
        roi_ratio = total_estimated_savings / system_cost if system_cost > 0 else 0
        
        return jsonify({
            "title": "Economic Impact Assessment",
            "dateRange": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "summary": {
                "totalDetections": total_detections,
                "totalPotentialLoss": round(total_potential_loss, 2),
                "totalEstimatedSavings": round(total_estimated_savings, 2),
                "roiRatio": round(roi_ratio, 2)
            },
            "tables": {
                "economicData": economic_data,
                "cropSummary": crop_summary_data,
                "provinceSummary": province_summary_data
            },
            "chartData": {
                "cropSavings": sorted(crop_summary_data, key=lambda x: x["savings"], reverse=True),
                "provinceSavings": sorted(province_summary_data, key=lambda x: x["savings"], reverse=True)
            },
            "methodology": {
                "assumptions": {
                    "avgFarmSize": avg_farm_size,
                    "earlyDetectionSavingsRate": "70%",
                    "systemCost": system_cost
                }
            }
        })
    
    def get_client_activity_data(self, start_date, end_date):
        """Return client activity data for the given date range"""
        # Query user activity data
        active_users = db.session.query(
            User.userId,
            User.username,
            func.count(DiagnosisResult.resultId).label('diagnosis_count'),
            func.max(DiagnosisResult.date).label('last_diagnosis')
        ).join(
            DiagnosisResult, User.userId == DiagnosisResult.userId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            User.userId, User.username
        ).order_by(
            desc('diagnosis_count')
        ).all()
        
        # Query activity trends over time
        activity_trends = db.session.query(
            func.date_trunc('day', DiagnosisResult.date).label('date'),
            func.count(func.distinct(DiagnosisResult.userId)).label('active_users'),
            func.count(DiagnosisResult.resultId).label('diagnoses')
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            'date'
        ).order_by(
            'date'
        ).all()
        
        # Format data for JSON response
        user_data = []
        for item in active_users:
            user_data.append({
                "userId": item[0],
                "username": item[1],
                "diagnosisCount": item[2],
                "lastDiagnosis": item[3].strftime('%Y-%m-%d') if item[3] else None
            })
        
        trend_data = []
        for item in activity_trends:
            trend_data.append({
                "date": item[0].strftime('%Y-%m-%d'),
                "activeUsers": item[1],
                "diagnoses": item[2]
            })
        
        # Calculate summary statistics
        total_active_users = len(user_data)
        total_diagnoses = sum(item["diagnosisCount"] for item in user_data)
        avg_diagnoses = round(total_diagnoses / total_active_users, 2) if total_active_users > 0 else 0
        
        # Get top users
        top_users = sorted(user_data, key=lambda x: x["diagnosisCount"], reverse=True)[:10]
        
        return jsonify({
            "title": "Client Activity Report",
            "dateRange": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "summary": {
                "totalActiveUsers": total_active_users,
                "totalDiagnoses": total_diagnoses,
                "avgDiagnosesPerUser": avg_diagnoses,
                "mostActiveUser": top_users[0]["username"] if top_users else "None"
            },
            "tables": {
                "activeUsers": user_data,
                "activityTrends": trend_data
            },
            "chartData": {
                "dailyActiveUsers": [
                    {"date": item["date"], "count": item["activeUsers"]} 
                    for item in trend_data
                ],
                "dailyDiagnoses": [
                    {"date": item["date"], "count": item["diagnoses"]} 
                    for item in trend_data
                ],
                "topUsers": [
                    {"username": item["username"], "count": item["diagnosisCount"]} 
                    for item in top_users
                ]
            }
        })
    
    def get_growth_analysis_data(self, start_date, end_date):
        """Return growth analysis data for the given date range"""
        # Query monthly growth data
        monthly_users = db.session.query(
            func.date_trunc('month', User.createdAt).label('month'),
            func.count(User.userId).label('new_users')
        ).filter(
            User.createdAt.between(start_date, end_date)
        ).group_by(
            'month'
        ).order_by(
            'month'
        ).all()
        
        monthly_diagnoses = db.session.query(
            func.date_trunc('month', DiagnosisResult.date).label('month'),
            func.count(DiagnosisResult.resultId).label('diagnoses')
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            'month'
        ).order_by(
            'month'
        ).all()
        
        monthly_communities = db.session.query(
            func.date_trunc('month', Community.createdAt).label('month'),
            func.count(Community.communityId).label('new_communities')
        ).filter(
            Community.createdAt.between(start_date, end_date)
        ).group_by(
            'month'
        ).order_by(
            'month'
        ).all()
        
        # Format data for JSON response
        user_growth = []
        for item in monthly_users:
            user_growth.append({
                "month": item[0].strftime('%Y-%m'),
                "newUsers": item[1]
            })
        
        diagnosis_growth = []
        for item in monthly_diagnoses:
            diagnosis_growth.append({
                "month": item[0].strftime('%Y-%m'),
                "diagnoses": item[1]
            })
        
        community_growth = []
        for item in monthly_communities:
            community_growth.append({
                "month": item[0].strftime('%Y-%m'),
                "newCommunities": item[1]
            })
        
        # Calculate growth rates
        growth_rates = []
        months = sorted(set([item["month"] for item in user_growth] + 
                          [item["month"] for item in diagnosis_growth] + 
                          [item["month"] for item in community_growth]))
        
        for i in range(1, len(months)):
            curr_month = months[i]
            prev_month = months[i-1]
            
            curr_users = next((item["newUsers"] for item in user_growth if item["month"] == curr_month), 0)
            prev_users = next((item["newUsers"] for item in user_growth if item["month"] == prev_month), 0)
            
            curr_diagnoses = next((item["diagnoses"] for item in diagnosis_growth if item["month"] == curr_month), 0)
            prev_diagnoses = next((item["diagnoses"] for item in diagnosis_growth if item["month"] == prev_month), 0)
            
            user_growth_rate = ((curr_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
            diagnosis_growth_rate = ((curr_diagnoses - prev_diagnoses) / prev_diagnoses * 100) if prev_diagnoses > 0 else 0
            
            growth_rates.append({
                "month": curr_month,
                "userGrowthRate": round(user_growth_rate, 2),
                "diagnosisGrowthRate": round(diagnosis_growth_rate, 2)
            })
        
        # Calculate summary statistics
        total_new_users = sum(item["newUsers"] for item in user_growth)
        total_diagnoses = sum(item["diagnoses"] for item in diagnosis_growth)
        total_new_communities = sum(item["newCommunities"] for item in community_growth)
        
        # Calculate average monthly growth rates
        avg_user_growth = sum(item["userGrowthRate"] for item in growth_rates) / len(growth_rates) if growth_rates else 0
        avg_diagnosis_growth = sum(item["diagnosisGrowthRate"] for item in growth_rates) / len(growth_rates) if growth_rates else 0
        
        return jsonify({
            "title": "Growth Analysis Report",
            "dateRange": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "summary": {
                "totalNewUsers": total_new_users,
                "totalDiagnoses": total_diagnoses,
                "totalNewCommunities": total_new_communities,
                "avgUserGrowthRate": round(avg_user_growth, 2),
                "avgDiagnosisGrowthRate": round(avg_diagnosis_growth, 2)
            },
            "tables": {
                "userGrowth": user_growth,
                "diagnosisGrowth": diagnosis_growth,
                "communityGrowth": community_growth,
                "growthRates": growth_rates
            },
            "chartData": {
                "userTrend": [
                    {"month": item["month"], "count": item["newUsers"]} 
                    for item in user_growth
                ],
                "diagnosisTrend": [
                    {"month": item["month"], "count": item["diagnoses"]} 
                    for item in diagnosis_growth
                ],
                "growthRateTrend": [
                    {"month": item["month"], "userRate": item["userGrowthRate"], "diagnosisRate": item["diagnosisGrowthRate"]} 
                    for item in growth_rates
                ]
            }
        })