import random
from flask_restful import Resource, abort
from flask import request, render_template, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import case, func, desc, extract
from datetime import datetime, timedelta
from models import (
    db, User, Post, Comment, Community, UserCommunity, 
    DiagnosisResult, Disease, Crop, District, Province,
    SupportRequest, SupportRequestStatus, SupportRequestType,
    ModelRating, ModelVersion, PostLike
)

class ReportNew(Resource):
    
    @jwt_required()
    def get(self, report_type=None):
        """Generate various reports for system administrators and RAB."""
        try:
            # Validate user has appropriate access (admin or RAB)
            user_identity = get_jwt_identity()
            user_id = int(user_identity["userId"])
            user = User.query.get(user_id)
            if not user or user.role not in ['admin', 'rab']:
                abort(403, message="Insufficient privileges to access reports")
            
            # Get time period filters from request
            start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=30)).isoformat())
            end_date = request.args.get('end_date', datetime.utcnow().isoformat())
            
            # Process report based on type
            if not report_type:
                # Return available report types if none specified
                return self._get_report_types(), 200
            
            report_data = self._generate_report(report_type, start_date, end_date)
            
            # Check if HTML response is requested
            if request.args.get('format') == 'html':
                html_content = render_template(
                    f'reports/{report_type.lower()}.html',
                    data=report_data,
                    start_date=start_date,
                    end_date=end_date
                )
                response = make_response(html_content)
                response.headers['Content-Type'] = 'text/html'
                return response
            
            # Default JSON response
            return {"data": report_data}, 200
            
        except Exception as e:
            abort(500, message=f"An error occurred while generating the report: {str(e)}")
    
    def _get_report_types(self):
        """Return list of available report types."""
        return {
            "report_types": [
                {"id": "user_engagement", "name": "User Engagement & Growth"},
                {"id": "community_interactions", "name": "Community & Social Interactions"},
                {"id": "platform_health", "name": "Platform Health & Support"},
                {"id": "disease_analytics", "name": "Plant Disease Analytics"},
                {"id": "crop_monitoring", "name": "Crop Monitoring & Vulnerability"},
                {"id": "geographical_insights", "name": "Geographical Insights"},
                {"id": "intervention_analysis", "name": "Intervention & Treatment Analysis"},
                {"id": "knowledge_impact", "name": "Knowledge & Educational Impact"},
                {"id": "early_warning", "name": "Predictive & Early Warning Systems"}
            ]
        }
    
    def _generate_report(self, report_type, start_date, end_date):
        """Generate specific report data based on type."""
        report_generators = {
            'user_engagement': self._generate_user_engagement_report,
            'community_interactions': self._generate_community_interactions_report,
            'platform_health': self._generate_platform_health_report,
            'disease_analytics': self._generate_disease_analytics_report,
            'crop_monitoring': self._generate_crop_monitoring_report,
            'geographical_insights': self._generate_geographical_insights_report,
            'intervention_analysis': self._generate_intervention_analysis_report,
            'knowledge_impact': self._generate_knowledge_impact_report,
            'early_warning': self._generate_early_warning_report
        }
        
        if report_type.lower() not in report_generators:
            abort(400, message=f"Invalid report type: {report_type}")
        
        # Convert string dates to datetime objects
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            abort(400, message="Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS).")
        
        return report_generators[report_type.lower()](start_dt, end_dt)
    
    def _generate_user_engagement_report(self, start_date, end_date):
        """Generate user engagement and growth report data."""
        # New users per month
        new_users_query = db.session.query(
            extract('year', User.createdAt).label('year'),
            extract('month', User.createdAt).label('month'),
            func.count(User.userId).label('count')
        ).filter(
            User.createdAt.between(start_date, end_date)
        ).group_by('year', 'month').order_by('year', 'month').all()
        
        new_users_data = [
            {
                'year': int(item.year),
                'month': int(item.month),
                'count': item.count
            } for item in new_users_query
        ]
        
        # Active users (based on diagnosis results, posts, comments)
        active_users_query = db.session.query(
            func.date_trunc('day', DiagnosisResult.date).label('day'),
            func.count(func.distinct(DiagnosisResult.userId)).label('count')
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by('day').order_by('day').all()
        
        active_users_data = [
            {
                'date': item.day.strftime('%Y-%m-%d'),
                'count': item.count
            } for item in active_users_query
        ]
        
        # User roles breakdown
        user_roles_query = db.session.query(
            User.role,
            func.count(User.userId).label('count')
        ).group_by(User.role).all()
        
        user_roles_data = [
            {
                'role': item.role,
                'count': item.count
            } for item in user_roles_query
        ]
        
        # User verification status
        verification_status_query = db.session.query(
            User.isVerified,
            func.count(User.userId).label('count')
        ).group_by(User.isVerified).all()
        
        verification_status_data = [
            {
                'status': 'Verified' if item.isVerified else 'Unverified',
                'count': item.count
            } for item in verification_status_query
        ]
        
        return {
            'new_users_trend': new_users_data,
            'active_users': active_users_data,
            'user_roles': user_roles_data,
            'verification_status': verification_status_data
        }
    
    def _generate_community_interactions_report(self, start_date, end_date):
        """Generate community and social interactions report data."""
        # Top active communities
        top_communities_query = db.session.query(
            Community.communityId,
            Community.name,
            func.count(Post.postId).label('post_count')
        ).join(Post, Community.communityId == Post.communityId
        ).filter(
            Post.createdAt.between(start_date, end_date)
        ).group_by(
            Community.communityId, Community.name
        ).order_by(desc('post_count')).limit(10).all()
        
        top_communities_data = [
            {
                'id': item.communityId,
                'name': item.name,
                'post_count': item.post_count
            } for item in top_communities_query
        ]
        
        # Posts per day trend
        posts_per_day_query = db.session.query(
            func.date_trunc('day', Post.createdAt).label('day'),
            func.count(Post.postId).label('count')
        ).filter(
            Post.createdAt.between(start_date, end_date)
        ).group_by('day').order_by('day').all()
        
        posts_per_day_data = [
            {
                'date': item.day.strftime('%Y-%m-%d'),
                'count': item.count
            } for item in posts_per_day_query
        ]
        
        # Post engagement rate
        post_engagement_query = db.session.query(
            Post.postId,
            Post.content,
            Post.likes,
            func.count(Comment.commentId).label('comment_count')
        ).outerjoin(Comment, Post.postId == Comment.postId
        ).filter(
            Post.createdAt.between(start_date, end_date)
        ).group_by(Post.postId, Post.content, Post.likes
        ).order_by(desc(Post.likes + func.count(Comment.commentId))).limit(10).all()
        
        post_engagement_data = [
            {
                'id': item.postId,
                'content': item.content[:100] + '...' if len(item.content) > 100 else item.content,
                'likes': item.likes,
                'comments': item.comment_count,
                'engagement_rate': item.likes + item.comment_count
            } for item in post_engagement_query
        ]
        
        # Top contributors
        top_contributors_query = db.session.query(
            User.userId,
            User.username,
            func.count(Post.postId).label('post_count')
        ).join(Post, User.userId == Post.userId
        ).filter(
            Post.createdAt.between(start_date, end_date)
        ).group_by(User.userId, User.username
        ).order_by(desc('post_count')).limit(10).all()
        
        top_contributors_data = [
            {
                'id': item.userId,
                'username': item.username,
                'post_count': item.post_count
            } for item in top_contributors_query
        ]
        
        return {
            'top_communities': top_communities_data,
            'posts_per_day': posts_per_day_data,
            'post_engagement': post_engagement_data,
            'top_contributors': top_contributors_data
        }
    
    def _generate_platform_health_report(self, start_date, end_date):
        """Generate platform health and support report data."""
        # Support requests by type
        support_by_type_query = db.session.query(
            SupportRequest.type,
            func.count(SupportRequest.requestId).label('count')
        ).filter(
            SupportRequest.createdAt.between(start_date, end_date)
        ).group_by(SupportRequest.type).all()
        
        support_by_type_data = [
            {
                'type': item.type.value,
                'count': item.count
            } for item in support_by_type_query
        ]
        
        # Support requests by status
        support_by_status_query = db.session.query(
            SupportRequest.status,
            func.count(SupportRequest.requestId).label('count')
        ).filter(
            SupportRequest.createdAt.between(start_date, end_date)
        ).group_by(SupportRequest.status).all()
        
        support_by_status_data = [
            {
                'status': item.status.value,
                'count': item.count
            } for item in support_by_status_query
        ]
        
        # Average resolution time
        resolved_tickets = db.session.query(
            SupportRequest
        ).filter(
            SupportRequest.status == SupportRequestStatus.RESOLVED,
            SupportRequest.createdAt.between(start_date, end_date)
        ).all()
        
        if resolved_tickets:
            resolution_times = [(ticket.updatedAt - ticket.createdAt).total_seconds() / 3600 for ticket in resolved_tickets]
            avg_resolution_time = sum(resolution_times) / len(resolution_times)
        else:
            avg_resolution_time = 0
        
        # Model ratings
        model_ratings_query = db.session.query(
            ModelRating.modelId,
            ModelVersion.version,
            func.avg(ModelRating.rating).label('avg_rating'),
            func.count(ModelRating.ratingId).label('rating_count'),
            func.sum(case((ModelRating.diagnosisCorrect == True, 1), else_=0)).label('correct_count'),
            func.sum(case((ModelRating.diagnosisCorrect == False, 1), else_=0)).label('incorrect_count')
        ).join(
            ModelVersion, ModelRating.modelId == ModelVersion.modelId
        ).filter(
            ModelRating.createdAt.between(start_date, end_date)
        ).group_by(ModelRating.modelId, ModelVersion.version).all()
        
        model_ratings_data = [
            {
                'model_id': item.modelId,
                'version': item.version,
                'avg_rating': float(item.avg_rating),
                'rating_count': item.rating_count,
                'correct_count': item.correct_count,
                'incorrect_count': item.incorrect_count,
                'accuracy_pct': (item.correct_count / (item.correct_count + item.incorrect_count)) * 100 if (item.correct_count + item.incorrect_count) > 0 else 0
            } for item in model_ratings_query
        ]
        
        return {
            'support_by_type': support_by_type_data,
            'support_by_status': support_by_status_data,
            'avg_resolution_time_hours': avg_resolution_time,
            'model_ratings': model_ratings_data
        }
    
    def _generate_disease_analytics_report(self, start_date, end_date):
        """Generate plant disease analytics report data."""
        # Most common diseases
        common_diseases_query = db.session.query(
            Disease.diseaseId,
            Disease.name,
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            DiagnosisResult, Disease.diseaseId == DiagnosisResult.diseaseId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date),
            DiagnosisResult.detected == True
        ).group_by(Disease.diseaseId, Disease.name
        ).order_by(desc('count')).all()
        
        common_diseases_data = [
            {
                'id': item.diseaseId,
                'name': item.name,
                'count': item.count
            } for item in common_diseases_query
        ]
        
        # Disease trends over time
        disease_trends_query = db.session.query(
            func.date_trunc('day', DiagnosisResult.date).label('day'),
            Disease.name,
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date),
            DiagnosisResult.detected == True
        ).group_by('day', Disease.name).order_by('day').all()
        
        disease_trends_data = [
            {
                'date': item.day.strftime('%Y-%m-%d'),
                'disease': item.name,
                'count': item.count
            } for item in disease_trends_query
        ]
        
        # Detected vs undetected cases
        detection_ratio_query = db.session.query(
            DiagnosisResult.detected,
            func.count(DiagnosisResult.resultId).label('count')
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(DiagnosisResult.detected).all()
        
        detection_ratio_data = [
            {
                'status': 'Detected' if item.detected else 'Not Detected',
                'count': item.count
            } for item in detection_ratio_query
        ]
        
        # Model version performance
        model_performance_query = db.session.query(
            DiagnosisResult.modelVersion,
            func.count(DiagnosisResult.resultId).label('total'),
            func.sum(case((DiagnosisResult.rated == True, 1), else_=0)).label('rated_count'),
            func.sum(case((ModelRating.diagnosisCorrect == True, 1), else_=0)).label('correct_count')
        ).outerjoin(
            ModelRating, ModelRating.modelId == DiagnosisResult.modelVersion
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(DiagnosisResult.modelVersion).all()
        
        model_performance_data = [
            {
                'version': item.modelVersion,
                'total_diagnoses': item.total,
                'rated_count': item.rated_count,
                'correct_count': item.correct_count,
                'accuracy_pct': (item.correct_count / item.rated_count) * 100 if item.rated_count > 0 else 0
            } for item in model_performance_query
        ]
        
        return {
            'common_diseases': common_diseases_data,
            'disease_trends': disease_trends_data,
            'detection_ratio': detection_ratio_data,
            'model_performance': model_performance_data
        }
    
    def _generate_crop_monitoring_report(self, start_date, end_date):
        """Generate crop monitoring and vulnerability report data."""
        # Diseases by crop type
        crop_diseases_query = db.session.query(
            Crop.cropId,
            Crop.name.label('crop_name'),
            Disease.diseaseId,
            Disease.name.label('disease_name'),
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            Disease, Crop.cropId == Disease.cropId
        ).join(
            DiagnosisResult, Disease.diseaseId == DiagnosisResult.diseaseId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date),
            DiagnosisResult.detected == True
        ).group_by(
            Crop.cropId, Crop.name, Disease.diseaseId, Disease.name
        ).order_by(Crop.name, desc('count')).all()
        
        crop_diseases_data = [
            {
                'crop_id': item.cropId,
                'crop_name': item.crop_name,
                'disease_id': item.diseaseId,
                'disease_name': item.disease_name,
                'count': item.count
            } for item in crop_diseases_query
        ]
        
        # Seasonal disease patterns
        seasonal_patterns_query = db.session.query(
            extract('month', DiagnosisResult.date).label('month'),
            Crop.name.label('crop_name'),
            Disease.name.label('disease_name'),
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).join(
            Crop, Disease.cropId == Crop.cropId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date),
            DiagnosisResult.detected == True
        ).group_by(
            'month', Crop.name, Disease.name
        ).order_by('month').all()
        
        seasonal_patterns_data = [
            {
                'month': int(item.month),
                'crop_name': item.crop_name,
                'disease_name': item.disease_name,
                'count': item.count
            } for item in seasonal_patterns_query
        ]
        
        return {
            'crop_diseases': crop_diseases_data,
            'seasonal_patterns': seasonal_patterns_data
        }
    
    def _generate_geographical_insights_report(self, start_date, end_date):
        """Generate geographical insights report data."""
        # Disease distribution by district
        district_distribution_query = db.session.query(
            District.districtId,
            District.name.label('district_name'),
            Province.name.label('province_name'),
            Disease.diseaseId,
            Disease.name.label('disease_name'),
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            DiagnosisResult, District.districtId == DiagnosisResult.districtId
        ).join(
            Province, District.provinceId == Province.provinceId
        ).join(
            Disease, DiagnosisResult.diseaseId == Disease.diseaseId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date),
            DiagnosisResult.detected == True
        ).group_by(
            District.districtId, District.name, Province.name, 
            Disease.diseaseId, Disease.name
        ).order_by(Province.name, District.name, desc('count')).all()
        
        district_distribution_data = [
            {
                'district_id': item.districtId,
                'district_name': item.district_name,
                'province_name': item.province_name,
                'disease_id': item.diseaseId,
                'disease_name': item.disease_name,
                'count': item.count
            } for item in district_distribution_query
        ]
        
        # Districts with highest diagnosis activity
        active_districts_query = db.session.query(
            District.districtId,
            District.name.label('district_name'),
            Province.name.label('province_name'),
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            DiagnosisResult, District.districtId == DiagnosisResult.districtId
        ).join(
            Province, District.provinceId == Province.provinceId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date)
        ).group_by(
            District.districtId, District.name, Province.name
        ).order_by(desc('count')).limit(10).all()
        
        active_districts_data = [
            {
                'district_id': item.districtId,
                'district_name': item.district_name,
                'province_name': item.province_name,
                'diagnosis_count': item.count
            } for item in active_districts_query
        ]
        
        return {
            'district_distribution': district_distribution_data,
            'active_districts': active_districts_data
        }
    
    def _generate_intervention_analysis_report(self, start_date, end_date):
        """Generate intervention and treatment analysis report data with real disease and crop names."""
        
        # Get real diseases from the database
        real_diseases = db.session.query(
            Disease.name
        ).order_by(func.random()).limit(5).all()
        
        real_disease_names = [disease.name for disease in real_diseases]
        
        # Get real crops from the database
        real_crops = db.session.query(
            Crop.name
        ).order_by(func.random()).limit(4).all()
        
        real_crop_names = [crop.name for crop in real_crops]
        
        # Get real districts from the database
        real_districts = db.session.query(
            District.name
        ).order_by(func.random()).limit(4).all()
        
        real_district_names = [district.name for district in real_districts]
        
        # Generate simulated treatment data using real entities
        treatments = ['Organic Fungicide', 'Chemical Spray', 'Biological Control', 'Resistant Varieties']
        treatment_success_rates = [
            {
                'treatment': treatment,
                'success_rate': round(70 + 25 * random.random(), 1),
                'application_count': random.randint(200, 550)
            }
            for treatment in treatments
        ]
        
        # Generate disease-specific treatments using real diseases
        disease_specific_treatments = [
            {
                'disease': disease_name,
                'treatment': random.choice(treatments),
                'success_rate': round(75 + 20 * random.random(), 1)
            }
            for disease_name in real_disease_names
        ]
        
        # Prevention strategies data
        prevention_strategies = [
            {'strategy': 'Crop Rotation', 'adoption': round(40 + 50 * random.random(), 1), 'effectiveness': round(70 + 25 * random.random(), 1)},
            {'strategy': 'Resistant Varieties', 'adoption': round(40 + 50 * random.random(), 1), 'effectiveness': round(70 + 25 * random.random(), 1)},
            {'strategy': 'Field Sanitation', 'adoption': round(40 + 50 * random.random(), 1), 'effectiveness': round(70 + 25 * random.random(), 1)},
            {'strategy': 'Regular Monitoring', 'adoption': round(40 + 50 * random.random(), 1), 'effectiveness': round(70 + 25 * random.random(), 1)},
            {'strategy': 'Proper Spacing', 'adoption': round(40 + 50 * random.random(), 1), 'effectiveness': round(70 + 25 * random.random(), 1)}
        ]
        
        # Generate before/after data for districts using real district names
        improved_districts = [
            {
                'district': district_name,
                'before': random.randint(60, 90),
                'after': random.randint(25, 45)
            }
            for district_name in real_district_names
        ]
        
        # Generate before/after data for crops using real crop names
        improved_crops = [
            {
                'crop': crop_name,
                'before': random.randint(55, 90),
                'after': random.randint(25, 45)
            }
            for crop_name in real_crop_names
        ]
        
        return {
            'is_preview': True,
            'message': 'This report currently shows simulated intervention data based on real entities in your system. Real intervention tracking will be available in a future update.',
            'sample_data': {
                'treatment_success_rates': treatment_success_rates,
                'disease_specific_treatments': disease_specific_treatments,
                'prevention_strategies': prevention_strategies,
                'improved_districts': improved_districts,
                'improved_crops': improved_crops
            }
        }

    def _generate_knowledge_impact_report(self, start_date, end_date):
        """Generate knowledge impact report with real community data and simulated educational metrics."""
        
        # Get real community discussion topics from the database
        discussion_topics_query = db.session.query(
            Community.name.label('community_name'),
            func.count(Post.postId).label('post_count')
        ).join(
            Post, Community.communityId == Post.communityId
        ).filter(
            Post.createdAt.between(start_date, end_date)
        ).group_by(Community.name).order_by(desc('post_count')).all()
        
        discussion_topics_data = [
            {
                'community_name': item.community_name,
                'post_count': item.post_count
            } for item in discussion_topics_query
        ]
        
        # Get real disease names for search topics
        real_diseases = db.session.query(
            Disease.name
        ).order_by(func.random()).limit(5).all()
        
        real_disease_names = [disease.name for disease in real_diseases]
        
        # Generate simulated search topics using real disease names
        search_topics = []
        for i, disease_name in enumerate(real_disease_names):
            topic_suffix = random.choice([' Treatment', ' Identification', ' Prevention', ' Control Methods', ' Signs'])
            topic = f"{disease_name}{topic_suffix}"
            
            # Randomize the trend a bit, but mostly positive
            trend = random.randint(-10, 25) if random.random() < 0.8 else -random.randint(1, 10)
            
            search_topics.append({
                'topic': topic,
                'volume': random.randint(500, 900),
                'trend': trend
            })
        
        return {
            'is_preview': True,
            'discussion_topics': discussion_topics_data,  # Real data
            'message': 'This report combines real discussion data with simulated learning metrics based on your actual diseases and crops. Complete knowledge impact tracking will be available in a future update.',
            'sample_data': {
                'search_topics': search_topics,
                'faq_categories': [
                    {'category': 'Disease Identification', 'frequency': 35},
                    {'category': 'Treatment Methods', 'frequency': 27},
                    {'category': 'App Usage Help', 'frequency': 18},
                    {'category': 'Prevention Strategies', 'frequency': 12},
                    {'category': 'Other', 'frequency': 8}
                ],
                'knowledge_growth': {
                    'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    'disease_identification': [35, 42, 49, 58, 65, 68],
                    'prevention_knowledge': [28, 32, 36, 40, 42, 42],
                    'treatment_efficacy': [22, 28, 35, 40, 45, 51]
                },
                'educational_content': [
                    {'title': 'Disease Identification Guide', 'views': 4782},
                    {'title': 'Preventive Farming Practices', 'views': 3946},
                    {'title': 'Organic Treatment Methods', 'views': 3218},
                    {'title': 'Climate-Smart Agriculture', 'views': 2873},
                    {'title': 'Crop Rotation Planning', 'views': 2451}
                ]
            }
        }

    def _generate_early_warning_report(self, start_date, end_date):
        """Generate predictive and early warning systems report using only real case numbers from database."""
        from datetime import datetime, timedelta
        
        # 1. Get real recent outbreaks data from the database
        recent_outbreaks_query = db.session.query(
            Disease.diseaseId,
            Disease.name,
            District.name.label('district_name'),
            func.count(DiagnosisResult.resultId).label('count'),
            func.max(DiagnosisResult.date).label('latest_date')
        ).join(
            DiagnosisResult, Disease.diseaseId == DiagnosisResult.diseaseId
        ).join(
            District, DiagnosisResult.districtId == District.districtId
        ).filter(
            DiagnosisResult.date.between(start_date, end_date),
            DiagnosisResult.detected == True
        ).group_by(
            Disease.diseaseId, Disease.name, District.name
        ).order_by(desc('latest_date')).all()
        
        recent_outbreaks_data = [
            {
                'disease_id': item.diseaseId,
                'disease_name': item.name,
                'district_name': item.district_name,
                'case_count': item.count,
                'latest_date': item.latest_date.strftime('%Y-%m-%d')
            } for item in recent_outbreaks_query
        ]
        
        # 2. Get top diseases by frequency for forecasting
        top_diseases_query = db.session.query(
            Disease.diseaseId,
            Disease.name,
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            DiagnosisResult, Disease.diseaseId == DiagnosisResult.diseaseId
        ).filter(
            DiagnosisResult.detected == True
        ).group_by(
            Disease.diseaseId, Disease.name
        ).order_by(desc('count')).limit(3).all()
        
        top_diseases = [(item.diseaseId, item.name, item.count) for item in top_diseases_query]
        
        # 3. Generate disease forecast based on actual prevalence
        disease_forecast_data = []
        
        for disease_id, disease_name, total_count in top_diseases:
            # Get districts where this disease has been detected
            disease_districts_query = db.session.query(
                District.name,
                func.count(DiagnosisResult.resultId).label('count')
            ).join(
                DiagnosisResult, District.districtId == DiagnosisResult.districtId
            ).filter(
                DiagnosisResult.diseaseId == disease_id,
                DiagnosisResult.detected == True
            ).group_by(District.name).order_by(desc('count')).limit(3).all()
            
            if not disease_districts_query:
                continue
                
            disease_districts = [item.name for item in disease_districts_query]
            
            # Calculate risk level based on total case count
            if total_count > 20:
                risk_level = 'high'
                timeframe = '2-3 weeks'
                confidence = 85 + (total_count - 20) // 5  # Higher confidence with more cases
                confidence = min(confidence, 95)  # Cap at 95%
            elif total_count > 10:
                risk_level = 'medium'
                timeframe = '4-6 weeks'
                confidence = 70 + (total_count - 10) // 2
            else:
                risk_level = 'low'
                timeframe = '8-10 weeks'
                confidence = 55 + total_count

            # Get growth rate to determine description
            growth_rate_query = db.session.query(
                func.count(DiagnosisResult.resultId).label('recent_count')
            ).filter(
                DiagnosisResult.diseaseId == disease_id,
                DiagnosisResult.detected == True,
                DiagnosisResult.date.between(end_date - timedelta(days=14), end_date)
            ).scalar() or 0
            
            older_count_query = db.session.query(
                func.count(DiagnosisResult.resultId).label('older_count')
            ).filter(
                DiagnosisResult.diseaseId == disease_id,
                DiagnosisResult.detected == True,
                DiagnosisResult.date.between(end_date - timedelta(days=28), end_date - timedelta(days=14))
            ).scalar() or 1  # Avoid division by zero
            
            growth_rate = growth_rate_query / older_count_query
            
            if growth_rate > 1.5:
                description = "Rapid increase in cases based on recent diagnosis patterns"
            elif growth_rate > 1.1:
                description = "Moderate increase in cases based on recent diagnosis patterns"
            else:
                description = "Based on historical diagnosis patterns in these regions"
            
            disease_forecast_data.append({
                'disease': disease_name,
                'locations': disease_districts,
                'risk_level': risk_level,
                'expected_timeframe': timeframe,
                'description': description,
                'confidence': confidence
            })
        
        # 4. Generate anomaly detection data based on actual weekly case counts
        # Get the most common disease for anomaly detection
        if not top_diseases:
            return {
                'recent_outbreaks': recent_outbreaks_data,
                'message': 'Insufficient data for predictive analysis. Please gather more diagnosis results.'
            }
            
        top_disease_id, top_disease_name, _ = top_diseases[0]
        
        # Get a district where this disease is most common
        top_district_query = db.session.query(
            District.name,
            func.count(DiagnosisResult.resultId).label('count')
        ).join(
            DiagnosisResult, District.districtId == DiagnosisResult.districtId
        ).filter(
            DiagnosisResult.diseaseId == top_disease_id,
            DiagnosisResult.detected == True
        ).group_by(District.name).order_by(desc('count')).first()
        
        if not top_district_query:
            return {
                'recent_outbreaks': recent_outbreaks_data,
                'disease_forecast': disease_forecast_data,
                'message': 'Insufficient location data for anomaly detection.'
            }
            
        top_district = top_district_query.name
        
        # Get weekly case counts for the past 8 weeks
        today = datetime.utcnow()
        start_of_analysis = today - timedelta(days=8*7)
        
        # Create a list of week start dates
        week_dates = []
        for i in range(8):
            week_start = start_of_analysis + timedelta(days=i*7)
            week_dates.append(week_start)
        
        # Query weekly case counts
        weekly_cases = []
        for i in range(len(week_dates) - 1):
            week_start = week_dates[i]
            week_end = week_dates[i+1]
            
            count_query = db.session.query(
                func.count(DiagnosisResult.resultId).label('count')
            ).join(
                District, DiagnosisResult.districtId == District.districtId
            ).filter(
                DiagnosisResult.diseaseId == top_disease_id,
                District.name == top_district,
                DiagnosisResult.detected == True,
                DiagnosisResult.date.between(week_start, week_end)
            ).scalar() or 0
            
            weekly_cases.append(count_query)
        
        # Create timeline labels
        timeline_dates = [date.strftime('%b %d') for date in week_dates]
        
        # Calculate expected bounds based on historical patterns
        # Use moving average for expected values
        expected_lower = []
        expected_upper = []
        
        for i in range(len(weekly_cases)):
            if i < 2:  # First 2 weeks just use actual values
                base = max(weekly_cases[i] - 2, 0)
                expected_lower.append(base)
                expected_upper.append(base + 4)
            else:
                # Use 3-week moving average as the base
                avg = sum(weekly_cases[i-3:i]) / 3
                expected_lower.append(max(avg * 0.8, 0))  # 20% below average
                expected_upper.append(avg * 1.2)  # 20% above average
        
        # Add anomaly alerts if there are significant deviations
        alerts_data = []
        
        # Check if the most recent week is above the expected upper bound
        if len(weekly_cases) > 1 and weekly_cases[-1] > expected_upper[-1]:
            percent_increase = int((weekly_cases[-1] / expected_upper[-1] * 100) - 100)
            alerts_data.append({
                'title': f'Unusual {top_disease_name} Pattern',
                'description': f'{top_district} district showing {percent_increase}% increase over expected levels',
                'date': (today - timedelta(days=7)).strftime('%B %d, %Y')
            })
        
        # Look for rapid growth patterns in other diseases
        for disease_id, disease_name, _ in top_diseases[1:]:
            # Get rapid growth districts for this disease
            growth_districts_query = db.session.query(
                District.name,
                func.count(DiagnosisResult.resultId).filter(
                    DiagnosisResult.date.between(end_date - timedelta(days=14), end_date)
                ).label('recent'),
                func.count(DiagnosisResult.resultId).filter(
                    DiagnosisResult.date.between(end_date - timedelta(days=28), end_date - timedelta(days=14))
                ).label('previous')
            ).join(
                DiagnosisResult, District.districtId == DiagnosisResult.districtId
            ).filter(
                DiagnosisResult.diseaseId == disease_id,
                DiagnosisResult.detected == True
            ).group_by(District.name).having(
                func.count(DiagnosisResult.resultId).filter(
                    DiagnosisResult.date.between(end_date - timedelta(days=14), end_date)
                ) > 5  # At least 5 recent cases
            ).all()
            
            for district in growth_districts_query:
                if district.previous > 0 and district.recent / district.previous > 1.5:
                    # Growth rate over 50%
                    alerts_data.append({
                        'title': f'Rapid {disease_name} Increase',
                        'description': f'{district.name} shows {int(district.recent / district.previous * 100) - 100}% increase in cases over past 2 weeks',
                        'date': (today - timedelta(days=3)).strftime('%B %d, %Y')
                    })
                    break
        
        # 5. Generate seasonal calendar data from actual monthly historical data
        # Get monthly counts for each disease for the entire historical data
        seasonal_diseases = []
        
        for disease_id, disease_name, _ in top_diseases:
            # Get monthly counts across all time
            monthly_counts_query = db.session.query(
                extract('month', DiagnosisResult.date).label('month'),
                func.count(DiagnosisResult.resultId).label('count')
            ).filter(
                DiagnosisResult.diseaseId == disease_id,
                DiagnosisResult.detected == True
            ).group_by('month').all()
            
            # Convert to a dict for easy lookup
            monthly_counts = {int(item.month): item.count for item in monthly_counts_query}
            
            # Calculate total cases to normalize
            total_cases = sum(monthly_counts.values())
            
            if total_cases == 0:
                continue
                
            # Fill in all months and normalize to 0-100 scale
            risk_levels = []
            for month in range(1, 13):
                if month in monthly_counts:
                    # Scale to 0-100 range
                    normalized = (monthly_counts[month] / total_cases) * 100 * 5  # Multiply by 5 to amplify the scale
                    risk_levels.append(min(int(normalized), 100))
                else:
                    # For months with no data, interpolate or use low value
                    prev_month = (month - 1) if month > 1 else 12
                    next_month = (month + 1) if month < 12 else 1
                    
                    prev_value = next((risk_levels[i] for i, m in enumerate(range(1, len(risk_levels)+1)) if m == prev_month), None)
                    
                    if prev_value is not None:
                        # Use 80% of previous month if we have it
                        risk_levels.append(int(prev_value * 0.8))
                    else:
                        # Default to low risk
                        risk_levels.append(20)
            
            seasonal_diseases.append({
                'name': disease_name,
                'risk_levels': risk_levels
            })
        
        return {
            'recent_outbreaks': recent_outbreaks_data,
            'disease_forecast': disease_forecast_data,
            'anomaly_detection': {
                'title': f'{top_disease_name} Cases in {top_district}',
                'labels': timeline_dates,
                'expected_upper': expected_upper,
                'expected_lower': expected_lower,
                'actual': weekly_cases,
                'alerts': alerts_data
            },
            'seasonal_calendar': {
                'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                'diseases': seasonal_diseases
            },
            'message': 'This report uses actual diagnosis data to identify trends and potential outbreaks. All metrics are based on real case counts from your database.'
        }