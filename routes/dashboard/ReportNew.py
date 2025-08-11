import os
import random
import tempfile
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
                {"id": "geographical_insights", "name": "Geographical Insights"}
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
        try:
            # Ensure dates are in datetime format
            if isinstance(start_date, str):
                try:
                    start_date = datetime.fromisoformat(start_date)
                except ValueError:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
            
            if isinstance(end_date, str):
                try:
                    end_date = datetime.fromisoformat(end_date)
                except ValueError:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    # Add a day to make it inclusive
                    end_date = end_date + timedelta(days=1)
            
            # Support requests by type
            support_by_type_data = []
            try:
                support_by_type_query = db.session.query(
                    SupportRequest.type,
                    func.count(SupportRequest.requestId).label('count')
                ).filter(
                    SupportRequest.createdAt.between(start_date, end_date)
                ).group_by(SupportRequest.type).all()
                
                for item in support_by_type_query:
                    try:
                        type_value = item.type.value if hasattr(item.type, 'value') else str(item.type)
                        support_by_type_data.append({
                            'type': type_value,
                            'count': item.count
                        })
                    except Exception as e:
                        print(f"Error processing support type: {e}")
            except Exception as e:
                print(f"Error querying support by type: {e}")
            
            # If still no data, try without date filtering
            if not support_by_type_data:
                try:
                    all_support_by_type = db.session.query(
                        SupportRequest.type,
                        func.count(SupportRequest.requestId).label('count')
                    ).group_by(SupportRequest.type).all()
                    
                    for item in all_support_by_type:
                        try:
                            type_value = item.type.value if hasattr(item.type, 'value') else str(item.type)
                            support_by_type_data.append({
                                'type': type_value,
                                'count': item.count,
                                'note': 'All-time data (date filter removed)'
                            })
                        except Exception as e:
                            print(f"Error processing all-time support type: {e}")
                except Exception as e:
                    print(f"Error querying all-time support by type: {e}")
            
            # Support requests by status
            support_by_status_data = []
            try:
                support_by_status_query = db.session.query(
                    SupportRequest.status,
                    func.count(SupportRequest.requestId).label('count')
                ).filter(
                    SupportRequest.createdAt.between(start_date, end_date)
                ).group_by(SupportRequest.status).all()
                
                for item in support_by_status_query:
                    try:
                        status_value = item.status.value if hasattr(item.status, 'value') else str(item.status)
                        support_by_status_data.append({
                            'status': status_value,
                            'count': item.count
                        })
                    except Exception as e:
                        print(f"Error processing support status: {e}")
            except Exception as e:
                print(f"Error querying support by status: {e}")
            
            # If still no data, try without date filtering
            if not support_by_status_data:
                try:
                    all_support_by_status = db.session.query(
                        SupportRequest.status,
                        func.count(SupportRequest.requestId).label('count')
                    ).group_by(SupportRequest.status).all()
                    
                    for item in all_support_by_status:
                        try:
                            status_value = item.status.value if hasattr(item.status, 'value') else str(item.status)
                            support_by_status_data.append({
                                'status': status_value,
                                'count': item.count,
                                'note': 'All-time data (date filter removed)'
                            })
                        except Exception as e:
                            print(f"Error processing all-time support status: {e}")
                except Exception as e:
                    print(f"Error querying all-time support by status: {e}")
            
            # Average resolution time
            avg_resolution_time = 0
            try:
                resolved_tickets = db.session.query(
                    SupportRequest
                ).filter(
                    SupportRequest.status == SupportRequestStatus.RESOLVED,
                    SupportRequest.createdAt.between(start_date, end_date),
                    SupportRequest.updatedAt != None
                ).all()
                
                if resolved_tickets:
                    resolution_times = []
                    for ticket in resolved_tickets:
                        try:
                            if ticket.updatedAt and ticket.createdAt:
                                resolution_times.append((ticket.updatedAt - ticket.createdAt).total_seconds() / 3600)
                        except Exception as e:
                            print(f"Error calculating resolution time: {e}")
                    
                    if resolution_times:
                        avg_resolution_time = sum(resolution_times) / len(resolution_times)
            except Exception as e:
                print(f"Error querying resolved tickets: {e}")
            
            # Model ratings
            model_ratings_data = []
            try:
                model_ratings_query = db.session.query(
                    ModelRating.modelId,
                    ModelVersion.version,
                    func.avg(ModelRating.rating).label('avg_rating'),
                    func.count(ModelRating.ratingId).label('rating_count'),
                    func.sum(case((ModelRating.diagnosisCorrect == True, 1), else_=0)).label('correct_count'),
                    func.sum(case((ModelRating.diagnosisCorrect == False, 1), else_=0)).label('incorrect_count')
                ).outerjoin(  # Changed to outer join to get ratings even if version is missing
                    ModelVersion, ModelRating.modelId == ModelVersion.modelId
                ).filter(
                    ModelRating.createdAt.between(start_date, end_date)
                ).group_by(ModelRating.modelId, ModelVersion.version).all()
                
                for item in model_ratings_query:
                    try:
                        correct_count = item.correct_count or 0
                        incorrect_count = item.incorrect_count or 0
                        total = correct_count + incorrect_count
                        
                        model_ratings_data.append({
                            'model_id': item.modelId,
                            'version': item.version or 'Unknown',
                            'avg_rating': float(item.avg_rating) if item.avg_rating is not None else 0,
                            'rating_count': item.rating_count or 0,
                            'correct_count': correct_count,
                            'incorrect_count': incorrect_count,
                            'accuracy_pct': (correct_count / total) * 100 if total > 0 else 0
                        })
                    except Exception as e:
                        print(f"Error processing model rating: {e}")
            except Exception as e:
                print(f"Error querying model ratings: {e}")
            
            # If still no model data, try without date filtering
            if not model_ratings_data:
                try:
                    all_model_ratings = db.session.query(
                        ModelRating.modelId,
                        func.avg(ModelRating.rating).label('avg_rating'),
                        func.count(ModelRating.ratingId).label('rating_count')
                    ).group_by(ModelRating.modelId).all()
                    
                    for item in all_model_ratings:
                        try:
                            model_ratings_data.append({
                                'model_id': item.modelId,
                                'version': 'Unknown',
                                'avg_rating': float(item.avg_rating) if item.avg_rating is not None else 0,
                                'rating_count': item.rating_count or 0,
                                'correct_count': 0,
                                'incorrect_count': 0,
                                'accuracy_pct': 0,
                                'note': 'All-time data (date filter removed)'
                            })
                        except Exception as e:
                            print(f"Error processing all-time model rating: {e}")
                except Exception as e:
                    print(f"Error querying all-time model ratings: {e}")
            
            # Get raw counts to help with debugging
            raw_counts = {
                'total_support_requests': db.session.query(func.count(SupportRequest.requestId)).scalar() or 0,
                'total_model_ratings': db.session.query(func.count(ModelRating.ratingId)).scalar() or 0,
                'filtered_support_requests': db.session.query(func.count(SupportRequest.requestId)).filter(
                    SupportRequest.createdAt.between(start_date, end_date)
                ).scalar() or 0,
                'filtered_model_ratings': db.session.query(func.count(ModelRating.ratingId)).filter(
                    ModelRating.createdAt.between(start_date, end_date)
                ).scalar() or 0
            }
            
            # If we still have no data at all, provide default values
            if not (support_by_type_data or support_by_status_data or model_ratings_data):
                return {
                    'support_by_type': [{'type': 'No Data', 'count': 0}],
                    'support_by_status': [{'status': 'No Data', 'count': 0}],
                    'avg_resolution_time_hours': 0,
                    'model_ratings': [{'model_id': 'None', 'version': 'None', 'avg_rating': 0, 'rating_count': 0, 
                                    'correct_count': 0, 'incorrect_count': 0, 'accuracy_pct': 0}],
                    'debug_info': {
                        'date_range': {
                            'start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
                            'end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date)
                        },
                        'raw_counts': raw_counts
                    }
                }
            
            return {
                'support_by_type': support_by_type_data,
                'support_by_status': support_by_status_data,
                'avg_resolution_time_hours': avg_resolution_time,
                'model_ratings': model_ratings_data,
                'debug_info': {
                    'date_range': {
                        'start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
                        'end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date)
                    },
                    'raw_counts': raw_counts
                }
            }
        
        except Exception as e:
            print(f"Critical error in platform health report: {e}")
            # Return a minimal response that won't break the UI
            return {
                'support_by_type': [{'type': 'Error', 'count': 0}],
                'support_by_status': [{'status': 'Error', 'count': 0}],
                'avg_resolution_time_hours': 0,
                'model_ratings': [{'model_id': 'Error', 'version': 'Error', 'avg_rating': 0, 'rating_count': 0,
                                'correct_count': 0, 'incorrect_count': 0, 'accuracy_pct': 0}],
                'error': str(e)
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
 
import matplotlib
matplotlib.use('Agg')  # Force non-interactive backend

# import io
from flask import request, make_response
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from matplotlib.ticker import MaxNLocator
import calendar
from collections import defaultdict

from reportlab.platypus import Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import base64
import io

class ReportPdf(Resource):
    """Resource for generating PDF reports from the report data."""
    
    def __init__(self):
        # Create an instance of the ReportNew class to use its report generation functions
        self.report_generator = ReportNew()
    
    @jwt_required()
    def get(self, report_type=None):
        """Generate PDF report for the specified report type."""
        try:
            # Validate user has appropriate access (admin or RAB)
            user_identity = get_jwt_identity()
            user_id = int(user_identity["userId"])
            user = User.query.get(user_id)
            if not user or user.role not in ['admin', 'rab']:
                abort(403, message="Insufficient privileges to access reports")
            
            if not report_type:
                abort(400, message="Report type is required")
            
            # Get time period filters from request
            start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=30)).isoformat())
            end_date = request.args.get('end_date', datetime.utcnow().isoformat())
            
            print(f"Request args: {request.args}")
            print(f"Using date strings: start_date={start_date}, end_date={end_date}")
            
            # Use the report generator's method to get the data for the specified report type
            # Pass the date strings directly - not datetime objects
            report_data = self.report_generator._generate_report(report_type, start_date, end_date)
            
            # Generate charts as PIL Images stored in memory
            chart_images = self._generate_chart_images(report_type, report_data)
            
            # Generate PDF using ReportLab
            buffer = self._generate_reportlab_pdf(report_type, report_data, chart_images, start_date, end_date)
            
            # Return PDF as response
            response = make_response(buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.pdf'
            
            return response
            
        except Exception as e:
            import traceback
            print(f"PDF Generation Error: {str(e)}")
            print(traceback.format_exc())  # Print full stack trace
            abort(500, message=f"An error occurred while generating the PDF report: {str(e)}")
    
    def _generate_reportlab_pdf(self, report_type, report_data, chart_images, start_date, end_date):
        """Generate a PDF using ReportLab."""
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading1']
        subheading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Custom styles
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            spaceAfter=12,
            spaceBefore=24,
            textColor=colors.blue,
            borderWidth=0,
            borderPadding=0,
            borderColor=colors.grey,
            borderRadius=None
        )
        
        # Content elements
        elements = []
        
        # Title
        report_title = self._get_report_title(report_type)
        elements.append(Paragraph(report_title, title_style))
        
        # Period
        elements.append(Paragraph(f"Period: {start_date} to {end_date}", normal_style))
        elements.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add sections based on report type
        if report_type == 'user_engagement':
            self._add_user_engagement_sections(elements, report_data, chart_images, styles, section_style, normal_style)
        elif report_type == 'community_interactions':
            self._add_community_interactions_sections(elements, report_data, chart_images, styles, section_style, normal_style)
        elif report_type == 'platform_health':
            self._add_platform_health_sections(elements, report_data, chart_images, styles, section_style, normal_style)
        elif report_type == 'disease_analytics':
            self._add_disease_analytics_sections(elements, report_data, chart_images, styles, section_style, normal_style)
        elif report_type == 'crop_monitoring':
            self._add_crop_monitoring_sections(elements, report_data, chart_images, styles, section_style, normal_style)
        elif report_type == 'geographical_insights':
            self._add_geographical_insights_sections(elements, report_data, chart_images, styles, section_style, normal_style)
        else:
            # Generic approach for unknown report types
            self._add_generic_sections(elements, report_data, styles, section_style, normal_style)
        
        try:
            # Build the PDF
            doc.build(elements)
        except Exception as e:
            print(f"Error building PDF: {str(e)}")
            # Create a simple error PDF
            buffer = io.BytesIO()
            simple_doc = SimpleDocTemplate(buffer, pagesize=A4)
            simple_elements = [
                Paragraph("Error Generating Report", title_style),
                Spacer(1, 0.25*inch),
                Paragraph(f"An error occurred while generating the report: {str(e)}", normal_style)
            ]
            simple_doc.build(simple_elements)
        
        # Return the buffer
        buffer.seek(0)
        return buffer
    
    def _add_user_engagement_sections(self, elements, data, chart_images, styles, section_style, normal_style):
        """Add sections for User Engagement report to the PDF."""
        # New Users Trend
        elements.append(Paragraph("User Growth Trend", section_style))
        
        if 'new_users_trend' in data and data['new_users_trend']:
            # Create table data
            table_data = [['Year', 'Month', 'New Users']]
            for item in data['new_users_trend']:
                table_data.append([str(item['year']), str(item['month']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'new_users_chart' in chart_images:
                self._add_chart_image(elements, chart_images['new_users_chart'], "New Users Trend")
        else:
            elements.append(Paragraph("No new user data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # Active Users
        elements.append(Paragraph("Active Users", section_style))
        
        if 'active_users' in data and data['active_users']:
            # Create table data
            table_data = [['Date', 'Active Users']]
            for item in data['active_users']:
                table_data.append([str(item['date']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'active_users_chart' in chart_images:
                self._add_chart_image(elements, chart_images['active_users_chart'], "Active Users")
        else:
            elements.append(Paragraph("No active user data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # User Roles
        elements.append(Paragraph("User Roles Distribution", section_style))
        
        if 'user_roles' in data and data['user_roles']:
            # Create table data
            table_data = [['Role', 'Count']]
            for item in data['user_roles']:
                table_data.append([str(item['role']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'user_roles_chart' in chart_images:
                self._add_chart_image(elements, chart_images['user_roles_chart'], "User Roles Distribution")
        else:
            elements.append(Paragraph("No user role data available.", normal_style))
        
        # Verification Status
        elements.append(Paragraph("User Verification Status", section_style))
        
        if 'verification_status' in data and data['verification_status']:
            # Create table data
            table_data = [['Status', 'Count']]
            for item in data['verification_status']:
                table_data.append([str(item['status']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'verification_status_chart' in chart_images:
                self._add_chart_image(elements, chart_images['verification_status_chart'], "Verification Status")
        else:
            elements.append(Paragraph("No verification status data available.", normal_style))
    
    def _add_community_interactions_sections(self, elements, data, chart_images, styles, section_style, normal_style):
        """Add sections for Community Interactions report to the PDF."""
        # Top Communities
        elements.append(Paragraph("Top Active Communities", section_style))
        
        if 'top_communities' in data and data['top_communities']:
            # Create table data
            table_data = [['Community Name', 'Post Count']]
            for item in data['top_communities']:
                table_data.append([str(item['name']), str(item['post_count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'top_communities_chart' in chart_images:
                self._add_chart_image(elements, chart_images['top_communities_chart'], "Top Communities")
        else:
            elements.append(Paragraph("No community data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # Posts Per Day
        elements.append(Paragraph("Posts Per Day", section_style))
        
        if 'posts_per_day' in data and data['posts_per_day']:
            # Create table data
            table_data = [['Date', 'Post Count']]
            for item in data['posts_per_day']:
                table_data.append([str(item['date']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'posts_per_day_chart' in chart_images:
                self._add_chart_image(elements, chart_images['posts_per_day_chart'], "Posts Per Day")
        else:
            elements.append(Paragraph("No post frequency data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # Post Engagement
        elements.append(Paragraph("Post Engagement", section_style))
        
        if 'post_engagement' in data and data['post_engagement']:
            # Create table data
            table_data = [['Content', 'Likes', 'Comments', 'Engagement Rate']]
            for item in data['post_engagement']:
                content = item['content']
                if len(content) > 50:
                    content = content[:47] + "..."
                table_data.append([content, str(item['likes']), str(item['comments']), str(item['engagement_rate'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'post_engagement_chart' in chart_images:
                self._add_chart_image(elements, chart_images['post_engagement_chart'], "Post Engagement")
        else:
            elements.append(Paragraph("No post engagement data available for the selected period.", normal_style))
        
        # Top Contributors
        elements.append(Paragraph("Top Contributors", section_style))
        
        if 'top_contributors' in data and data['top_contributors']:
            # Create table data
            table_data = [['Username', 'Post Count']]
            for item in data['top_contributors']:
                table_data.append([str(item['username']), str(item['post_count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'top_contributors_chart' in chart_images:
                self._add_chart_image(elements, chart_images['top_contributors_chart'], "Top Contributors")
        else:
            elements.append(Paragraph("No contributor data available for the selected period.", normal_style))
    
    def _add_platform_health_sections(self, elements, data, chart_images, styles, section_style, normal_style):
        """Add sections for Platform Health report to the PDF."""
        # Support Requests by Type
        elements.append(Paragraph("Support Requests by Type", section_style))
        
        if 'support_by_type' in data and data['support_by_type']:
            # Create table data
            table_data = [['Support Type', 'Count']]
            for item in data['support_by_type']:
                table_data.append([str(item['type']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'support_type_chart' in chart_images:
                self._add_chart_image(elements, chart_images['support_type_chart'], "Support by Type")
        else:
            elements.append(Paragraph("No support request type data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # Support Requests by Status
        elements.append(Paragraph("Support Requests by Status", section_style))
        
        if 'support_by_status' in data and data['support_by_status']:
            # Create table data
            table_data = [['Status', 'Count']]
            for item in data['support_by_status']:
                table_data.append([str(item['status']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'support_status_chart' in chart_images:
                self._add_chart_image(elements, chart_images['support_status_chart'], "Support by Status")
        else:
            elements.append(Paragraph("No support request status data available for the selected period.", normal_style))
        
        # Average Resolution Time
        elements.append(Paragraph("Average Resolution Time", section_style))
        elements.append(Paragraph(f"Average time to resolve support requests: {data.get('avg_resolution_time_hours', 0):.2f} hours", normal_style))
        
        elements.append(PageBreak())
        
        # Model Performance Ratings
        elements.append(Paragraph("Model Performance Ratings", section_style))
        
        if 'model_ratings' in data and data['model_ratings']:
            # Create table data
            table_data = [['Model Version', 'Avg Rating', 'Total Ratings', 'Correct Diagnoses', 'Incorrect Diagnoses', 'Accuracy %']]
            for item in data['model_ratings']:
                table_data.append([
                    str(item['version']),
                    f"{item['avg_rating']:.1f}",
                    str(item['rating_count']),
                    str(item['correct_count']),
                    str(item['incorrect_count']),
                    f"{item['accuracy_pct']:.1f}%"
                ])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add charts if available
            if 'model_ratings_chart' in chart_images:
                self._add_chart_image(elements, chart_images['model_ratings_chart'], "Model Ratings")
            
            if 'model_accuracy_chart' in chart_images:
                self._add_chart_image(elements, chart_images['model_accuracy_chart'], "Model Accuracy")
        else:
            elements.append(Paragraph("No model rating data available for the selected period.", normal_style))
    
    def _add_disease_analytics_sections(self, elements, data, chart_images, styles, section_style, normal_style):
        """Add sections for Disease Analytics report to the PDF."""
        # Most Common Diseases
        elements.append(Paragraph("Most Common Diseases", section_style))
        
        if 'common_diseases' in data and data['common_diseases']:
            # Create table data
            table_data = [['Disease', 'Count']]
            for item in data['common_diseases']:
                table_data.append([str(item['name']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'common_diseases_chart' in chart_images:
                self._add_chart_image(elements, chart_images['common_diseases_chart'], "Common Diseases")
        else:
            elements.append(Paragraph("No disease data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # Disease Trends
        elements.append(Paragraph("Disease Trends Over Time", section_style))
        
        if 'disease_trends' in data and data['disease_trends']:
            # Create table data
            table_data = [['Date', 'Disease', 'Count']]
            for item in data['disease_trends']:
                table_data.append([str(item['date']), str(item['disease']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'disease_trends_chart' in chart_images:
                self._add_chart_image(elements, chart_images['disease_trends_chart'], "Disease Trends")
        else:
            elements.append(Paragraph("No disease trend data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # Detection Ratio
        elements.append(Paragraph("Detection Ratio", section_style))
        
        if 'detection_ratio' in data and data['detection_ratio']:
            # Create table data
            table_data = [['Status', 'Count']]
            for item in data['detection_ratio']:
                table_data.append([str(item['status']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'detection_ratio_chart' in chart_images:
                self._add_chart_image(elements, chart_images['detection_ratio_chart'], "Detection Ratio")
        else:
            elements.append(Paragraph("No detection ratio data available for the selected period.", normal_style))
        
        # Model Version Performance
        elements.append(Paragraph("Model Version Performance", section_style))
        
        if 'model_performance' in data and data['model_performance']:
            # Create table data
            table_data = [['Version', 'Total Diagnoses', 'Rated Count', 'Correct Count', 'Accuracy %']]
            for item in data['model_performance']:
                table_data.append([
                    str(item['version']),
                    str(item['total_diagnoses']),
                    str(item['rated_count']),
                    str(item['correct_count']),
                    f"{item['accuracy_pct']:.1f}%"
                ])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'model_performance_chart' in chart_images:
                self._add_chart_image(elements, chart_images['model_performance_chart'], "Model Performance")
        else:
            elements.append(Paragraph("No model performance data available for the selected period.", normal_style))
    
    def _add_crop_monitoring_sections(self, elements, data, chart_images, styles, section_style, normal_style):
        """Add sections for Crop Monitoring report to the PDF."""
        # Diseases by Crop Type
        elements.append(Paragraph("Diseases by Crop Type", section_style))
        
        if 'crop_diseases' in data and data['crop_diseases']:
            # Create table data
            table_data = [['Crop', 'Disease', 'Count']]
            for item in data['crop_diseases']:
                table_data.append([str(item['crop_name']), str(item['disease_name']), str(item['count'])])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'crop_diseases_chart' in chart_images:
                self._add_chart_image(elements, chart_images['crop_diseases_chart'], "Crop Diseases")
        else:
            elements.append(Paragraph("No crop disease data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # Seasonal Disease Patterns
        elements.append(Paragraph("Seasonal Disease Patterns", section_style))
        
        if 'seasonal_patterns' in data and data['seasonal_patterns']:
            # Create table data
            table_data = [['Month', 'Crop', 'Disease', 'Count']]
            for item in data['seasonal_patterns']:
                table_data.append([
                    str(item['month']),
                    str(item['crop_name']),
                    str(item['disease_name']),
                    str(item['count'])
                ])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'seasonal_patterns_chart' in chart_images:
                self._add_chart_image(elements, chart_images['seasonal_patterns_chart'], "Seasonal Patterns")
        else:
            elements.append(Paragraph("No seasonal pattern data available for the selected period.", normal_style))
    
    def _add_geographical_insights_sections(self, elements, data, chart_images, styles, section_style, normal_style):
        """Add sections for Geographical Insights report to the PDF."""
        # Disease Distribution by District
        elements.append(Paragraph("Disease Distribution by District", section_style))
        
        if 'district_distribution' in data and data['district_distribution']:
            # Create table data
            table_data = [['District', 'Province', 'Disease', 'Count']]
            for item in data['district_distribution']:
                table_data.append([
                    str(item['district_name']),
                    str(item['province_name']),
                    str(item['disease_name']),
                    str(item['count'])
                ])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'district_distribution_chart' in chart_images:
                self._add_chart_image(elements, chart_images['district_distribution_chart'], "District Distribution")
        else:
            elements.append(Paragraph("No district distribution data available for the selected period.", normal_style))
        
        elements.append(PageBreak())
        
        # Districts with Highest Diagnosis Activity
        elements.append(Paragraph("Districts with Highest Diagnosis Activity", section_style))
        
        if 'active_districts' in data and data['active_districts']:
            # Create table data
            table_data = [['District', 'Province', 'Diagnosis Count']]
            for item in data['active_districts']:
                table_data.append([
                    str(item['district_name']),
                    str(item['province_name']),
                    str(item['diagnosis_count'])
                ])
            
            # Add table
            self._add_table(elements, table_data)
            
            # Add chart if available
            if 'active_districts_chart' in chart_images:
                self._add_chart_image(elements, chart_images['active_districts_chart'], "Active Districts")
        else:
            elements.append(Paragraph("No active district data available for the selected period.", normal_style))
    
    def _add_generic_sections(self, elements, data, styles, section_style, normal_style):
        """Add generic sections for any other report type."""
        for section_name, section_data in data.items():
            # Add section title
            elements.append(Paragraph(section_name.replace('_', ' ').title(), section_style))
            
            if isinstance(section_data, dict):
                # Create table for dict data
                table_data = [[key.replace('_', ' ').title(), str(value)] for key, value in section_data.items()]
                self._add_table(elements, table_data)
            
            elif isinstance(section_data, list) and section_data:
                if isinstance(section_data[0], dict):
                    # Create table for list of dicts
                    headers = [key.replace('_', ' ').title() for key in section_data[0].keys()]
                    table_data = [headers]
                    
                    for item in section_data:
                        row = [str(value) for value in item.values()]
                        table_data.append(row)
                    
                    self._add_table(elements, table_data)
                else:
                    # Simple list
                    for item in section_data:
                        elements.append(Paragraph(str(item), normal_style))
            else:
                # Simple value
                elements.append(Paragraph(str(section_data), normal_style))
            
            elements.append(Spacer(1, 0.25*inch))
    
    def _add_table(self, elements, table_data):
        """Add a formatted table to the PDF elements."""
        if not table_data:
            return
        
        try:
            # Create the table
            table = Table(table_data)
            
            # Style the table
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ])
            
            table.setStyle(style)
            
            # Add table to elements
            elements.append(table)
            elements.append(Spacer(1, 0.25*inch))
        except Exception as e:
            print(f"Error adding table: {str(e)}")
            elements.append(Paragraph("Error displaying table data", ParagraphStyle(
                'ErrorText',
                parent=getSampleStyleSheet()['Normal'],
                textColor=colors.red
            )))
            elements.append(Spacer(1, 0.25*inch))
    
    def _add_chart_image(self, elements, img_buffer, caption=None):
        """Add a chart image to the PDF elements properly using ReportLab Image."""
        try:
            # Reset buffer to start
            img_buffer.seek(0)

            # Create an Image flowable directly from the buffer
            img = Image(img_buffer, width=6*inch, height=3*inch)  # Adjust height as needed
            img.hAlign = 'CENTER'
            elements.append(img)

            # Add caption if provided
            if caption:
                elements.append(Paragraph(
                    f"<i>{caption}</i>",
                    ParagraphStyle(
                        'Caption',
                        parent=getSampleStyleSheet()['Normal'],
                        alignment=1,  # Center alignment
                        fontSize=9
                    )
                ))

            elements.append(Spacer(1, 0.25 * inch))

        except Exception as e:
            # Log the error but continue without the image
            print(f"Error adding chart image: {str(e)}")
            elements.append(Paragraph(
                f"[Chart '{caption or ''}' could not be displayed]",
                ParagraphStyle(
                    'ErrorText',
                    parent=getSampleStyleSheet()['Normal'],
                    textColor=colors.red
                )
            ))
            elements.append(Spacer(1, 0.25 * inch))
    
    def _get_report_title(self, report_type):
        """Get a human-readable title for the report."""
        titles = {
            'user_engagement': 'User Engagement & Growth Report',
            'community_interactions': 'Community & Social Interactions Report',
            'platform_health': 'Platform Health & Support Report',
            'disease_analytics': 'Plant Disease Analytics Report',
            'crop_monitoring': 'Crop Monitoring & Vulnerability Report',
            'geographical_insights': 'Geographical Insights Report'
        }
        
        return titles.get(report_type.lower(), f'{report_type.title()} Report')
    
    def _generate_chart_images(self, report_type, report_data):
        """Generate chart images for the report based on report type."""
        chart_generators = {
            'user_engagement': self._generate_user_engagement_charts,
            'community_interactions': self._generate_community_interactions_charts,
            'platform_health': self._generate_platform_health_charts,
            'disease_analytics': self._generate_disease_analytics_charts,
            'crop_monitoring': self._generate_crop_monitoring_charts,
            'geographical_insights': self._generate_geographical_insights_charts
        }
        
        if report_type.lower() not in chart_generators:
            return {}  # No charts for unknown report types
        
        return chart_generators[report_type.lower()](report_data)
    
    def _generate_user_engagement_charts(self, report_data):
        """Generate charts for user engagement report."""
        charts = {}
        
        # 1. New users trend (line chart)
        if 'new_users_trend' in report_data and report_data['new_users_trend']:
            try:
                # Sort data by year and month
                sorted_data = sorted(report_data['new_users_trend'], key=lambda x: (x['year'], x['month']))
                labels = [f"{item['year']}-{item['month']:02d}" for item in sorted_data]
                values = [item['count'] for item in sorted_data]
                
                plt.figure(figsize=(10, 6))
                plt.plot(labels, values, marker='o', linestyle='-', color='royalblue')
                plt.title('New Users Trend')
                plt.xlabel('Month')
                plt.ylabel('Number of New Users')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45, ha='right')
                
                # Add value annotations
                for i, val in enumerate(values):
                    plt.annotate(f'{val}', (labels[i], values[i]), 
                                textcoords="offset points", xytext=(0,10), ha='center')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['new_users_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating new users chart: {str(e)}")
        
        # 2. Active users (line chart)
        if 'active_users' in report_data and report_data['active_users']:
            try:
                dates = [item['date'] for item in report_data['active_users']]
                counts = [item['count'] for item in report_data['active_users']]
                
                plt.figure(figsize=(10, 6))
                plt.plot(dates, counts, marker='o', linestyle='-', color='green')
                plt.title('Active Users Per Day')
                plt.xlabel('Date')
                plt.ylabel('Number of Active Users')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45, ha='right')
                
                # Add value annotations
                for i, val in enumerate(counts):
                    plt.annotate(f'{val}', (dates[i], counts[i]), 
                                textcoords="offset points", xytext=(0,10), ha='center')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['active_users_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating active users chart: {str(e)}")
        
        # 3. User roles (pie chart)
        if 'user_roles' in report_data and report_data['user_roles']:
            try:
                labels = [item['role'].capitalize() for item in report_data['user_roles']]
                values = [item['count'] for item in report_data['user_roles']]
                
                plt.figure(figsize=(8, 8))
                
                # Create pie chart with percentages and values
                def make_autopct(values):
                    def my_autopct(pct):
                        total = sum(values)
                        val = int(round(pct*total/100.0))
                        return f'{pct:.1f}%\n({val:d})'
                    return my_autopct
                
                plt.pie(values, labels=labels, autopct=make_autopct(values), 
                       startangle=90, shadow=True, 
                       wedgeprops={'edgecolor': 'white', 'linewidth': 1})
                
                plt.axis('equal')
                plt.title('User Roles Distribution')
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['user_roles_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating user roles chart: {str(e)}")
        
        # 4. Verification status (pie chart)
        if 'verification_status' in report_data and report_data['verification_status']:
            try:
                labels = [item['status'] for item in report_data['verification_status']]
                values = [item['count'] for item in report_data['verification_status']]
                
                plt.figure(figsize=(8, 8))
                
                # Create pie chart with percentages and values
                def make_autopct(values):
                    def my_autopct(pct):
                        total = sum(values)
                        val = int(round(pct*total/100.0))
                        return f'{pct:.1f}%\n({val:d})'
                    return my_autopct
                
                plt.pie(values, labels=labels, autopct=make_autopct(values), 
                       startangle=90, shadow=True, 
                       wedgeprops={'edgecolor': 'white', 'linewidth': 1})
                
                plt.axis('equal')
                plt.title('User Verification Status')
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['verification_status_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating verification status chart: {str(e)}")
        
        return charts
    
    def _generate_community_interactions_charts(self, report_data):
        """Generate charts for community interactions report."""
        charts = {}
        
        # 1. Top communities (horizontal bar chart)
        if 'top_communities' in report_data and report_data['top_communities']:
            try:
                # Sort by post count descending
                sorted_data = sorted(report_data['top_communities'], key=lambda x: x['post_count'], reverse=True)
                names = [item['name'] for item in sorted_data]
                post_counts = [item['post_count'] for item in sorted_data]
                
                plt.figure(figsize=(10, max(6, len(names) * 0.4)))
                bars = plt.barh(names, post_counts, color='lightgreen')
                plt.title('Top Active Communities')
                plt.xlabel('Number of Posts')
                plt.ylabel('Community')
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    plt.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                            f'{width}', ha='left', va='center')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['top_communities_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating top communities chart: {str(e)}")
        
        # 2. Posts per day (line chart)
        if 'posts_per_day' in report_data and report_data['posts_per_day']:
            try:
                dates = [item['date'] for item in report_data['posts_per_day']]
                counts = [item['count'] for item in report_data['posts_per_day']]
                
                plt.figure(figsize=(10, 6))
                plt.plot(dates, counts, marker='o', linestyle='-', color='royalblue')
                plt.title('Posts Per Day')
                plt.xlabel('Date')
                plt.ylabel('Number of Posts')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45, ha='right')
                
                # Add value annotations
                for i, val in enumerate(counts):
                    plt.annotate(f'{val}', (dates[i], counts[i]), 
                                textcoords="offset points", xytext=(0,10), ha='center')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['posts_per_day_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating posts per day chart: {str(e)}")
        
        # 3. Post engagement (stacked bar chart)
        if 'post_engagement' in report_data and report_data['post_engagement']:
            try:
                # Get top 5 for clearer visualization
                top_posts = sorted(report_data['post_engagement'], key=lambda x: x['engagement_rate'], reverse=True)[:5]
                post_ids = [f"Post {item['id']}" for item in top_posts]
                likes = [item['likes'] for item in top_posts]
                comments = [item['comments'] for item in top_posts]
                
                plt.figure(figsize=(10, 6))
                
                x = np.arange(len(post_ids))
                width = 0.6
                
                plt.bar(x, likes, width, label='Likes', color='royalblue')
                plt.bar(x, comments, width, bottom=likes, label='Comments', color='lightgreen')
                
                plt.xlabel('Post ID')
                plt.ylabel('Engagement Count')
                plt.title('Top Posts by Engagement')
                plt.xticks(x, post_ids, rotation=45, ha='right')
                plt.legend()
                
                # Add total value annotations
                for i in range(len(post_ids)):
                    total = likes[i] + comments[i]
                    plt.annotate(f'{total}', (x[i], total), 
                                textcoords="offset points", xytext=(0,5), ha='center')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['post_engagement_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating post engagement chart: {str(e)}")
        
        # 4. Top contributors (horizontal bar chart)
        if 'top_contributors' in report_data and report_data['top_contributors']:
            try:
                # Sort by post count descending
                sorted_data = sorted(report_data['top_contributors'], key=lambda x: x['post_count'], reverse=True)
                usernames = [item['username'] for item in sorted_data]
                post_counts = [item['post_count'] for item in sorted_data]
                
                plt.figure(figsize=(10, max(6, len(usernames) * 0.4)))
                bars = plt.barh(usernames, post_counts, color='salmon')
                plt.title('Top Contributors')
                plt.xlabel('Number of Posts')
                plt.ylabel('Username')
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    plt.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                            f'{width}', ha='left', va='center')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['top_contributors_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating top contributors chart: {str(e)}")
        
        return charts
    
    def _generate_platform_health_charts(self, report_data):
        """Generate charts for platform health report."""
        charts = {}
        
        # 1. Support requests by type (bar chart)
        if 'support_by_type' in report_data and report_data['support_by_type']:
            try:
                # Sort by count descending
                sorted_data = sorted(report_data['support_by_type'], key=lambda x: x['count'], reverse=True)
                types = [item['type'] for item in sorted_data]
                counts = [item['count'] for item in sorted_data]
                
                plt.figure(figsize=(10, 6))
                bars = plt.bar(types, counts, color='skyblue')
                plt.title('Support Requests by Type')
                plt.xlabel('Type')
                plt.ylabel('Count')
                plt.xticks(rotation=45, ha='right')
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height}', ha='center', va='bottom')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['support_type_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating support type chart: {str(e)}")
        
        # 2. Support requests by status (pie chart)
        if 'support_by_status' in report_data and report_data['support_by_status']:
            try:
                statuses = [item['status'] for item in report_data['support_by_status']]
                counts = [item['count'] for item in report_data['support_by_status']]
                
                plt.figure(figsize=(8, 8))
                
                # Create pie chart with percentages and values
                def make_autopct(values):
                    def my_autopct(pct):
                        total = sum(values)
                        val = int(round(pct*total/100.0))
                        return f'{pct:.1f}%\n({val:d})'
                    return my_autopct
                
                plt.pie(counts, labels=statuses, autopct=make_autopct(counts), 
                       startangle=90, shadow=True, 
                       wedgeprops={'edgecolor': 'white', 'linewidth': 1})
                
                plt.axis('equal')
                plt.title('Support Requests by Status')
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['support_status_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating support status chart: {str(e)}")
        
        # 3. Model ratings (bar chart)
        if 'model_ratings' in report_data and report_data['model_ratings']:
            try:
                versions = [item['version'] for item in report_data['model_ratings']]
                avg_ratings = [item['avg_rating'] for item in report_data['model_ratings']]
                
                plt.figure(figsize=(10, 6))
                bars = plt.bar(versions, avg_ratings, color='lightgreen')
                plt.title('Average Model Ratings')
                plt.xlabel('Model Version')
                plt.ylabel('Rating (1-5)')
                plt.ylim(0, 5)  # Ratings typically 1-5
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.1f}', ha='center', va='bottom')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['model_ratings_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating model ratings chart: {str(e)}")
        
        # 4. Model accuracy (bar chart)
        if 'model_ratings' in report_data and report_data['model_ratings']:
            try:
                versions = [item['version'] for item in report_data['model_ratings']]
                accuracy = [item['accuracy_pct'] for item in report_data['model_ratings']]
                
                plt.figure(figsize=(10, 6))
                bars = plt.bar(versions, accuracy, color='salmon')
                plt.title('Model Diagnosis Accuracy')
                plt.xlabel('Model Version')
                plt.ylabel('Accuracy %')
                plt.ylim(0, 100)
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{height:.1f}%', ha='center', va='bottom')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['model_accuracy_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating model accuracy chart: {str(e)}")
        
        return charts
    
    def _generate_disease_analytics_charts(self, report_data):
        """Generate charts for disease analytics report."""
        charts = {}
        
        # 1. Most common diseases (horizontal bar chart)
        if 'common_diseases' in report_data and report_data['common_diseases']:
            try:
                # Sort by count descending
                sorted_data = sorted(report_data['common_diseases'], key=lambda x: x['count'], reverse=True)
                disease_names = [item['name'] for item in sorted_data]
                counts = [item['count'] for item in sorted_data]
                
                plt.figure(figsize=(10, max(6, len(disease_names) * 0.4)))
                bars = plt.barh(disease_names, counts, color='lightgreen')
                plt.title('Most Common Diseases')
                plt.xlabel('Number of Diagnoses')
                plt.ylabel('Disease')
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    plt.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                            f'{width}', ha='left', va='center')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['common_diseases_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating common diseases chart: {str(e)}")
        
        # 2. Disease trends over time (line chart with multiple lines)
        if 'disease_trends' in report_data and report_data['disease_trends']:
            try:
                # Group by date and disease
                disease_data = defaultdict(list)
                
                for item in report_data['disease_trends']:
                    disease_data[item['disease']].append((item['date'], item['count']))
                
                plt.figure(figsize=(12, 6))
                
                for disease, data_points in disease_data.items():
                    data_points.sort(key=lambda x: x[0])  # Sort by date
                    x_values = [point[0] for point in data_points]
                    y_values = [point[1] for point in data_points]
                    plt.plot(x_values, y_values, marker='o', label=disease)
                
                plt.title('Disease Trends Over Time')
                plt.xlabel('Date')
                plt.ylabel('Number of Diagnoses')
                plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['disease_trends_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating disease trends chart: {str(e)}")
        
        # 3. Detection ratio (pie chart)
        if 'detection_ratio' in report_data and report_data['detection_ratio']:
            try:
                statuses = [item['status'] for item in report_data['detection_ratio']]
                counts = [item['count'] for item in report_data['detection_ratio']]
                
                plt.figure(figsize=(8, 8))
                
                # Create pie chart with percentages and values
                def make_autopct(values):
                    def my_autopct(pct):
                        total = sum(values)
                        val = int(round(pct*total/100.0))
                        return f'{pct:.1f}%\n({val:d})'
                    return my_autopct
                
                plt.pie(counts, labels=statuses, autopct=make_autopct(counts), 
                       startangle=90, shadow=True, 
                       wedgeprops={'edgecolor': 'white', 'linewidth': 1})
                
                plt.axis('equal')
                plt.title('Disease Detection Ratio')
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['detection_ratio_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating detection ratio chart: {str(e)}")
        
        # 4. Model version performance (bar chart with dual y-axis)
        if 'model_performance' in report_data and report_data['model_performance']:
            try:
                versions = [item['version'] for item in report_data['model_performance']]
                diagnoses = [item['total_diagnoses'] for item in report_data['model_performance']]
                accuracy = [item['accuracy_pct'] for item in report_data['model_performance']]
                
                # Create dual-axis chart
                fig, ax1 = plt.subplots(figsize=(12, 6))
                
                # Plot total diagnoses as bars
                x = np.arange(len(versions))
                width = 0.4
                ax1.bar(x, diagnoses, width, color='steelblue', label='Total Diagnoses')
                ax1.set_xlabel('Model Version')
                ax1.set_ylabel('Number of Diagnoses', color='steelblue')
                ax1.tick_params(axis='y', labelcolor='steelblue')
                
                # Create second y-axis for accuracy
                ax2 = ax1.twinx()
                ax2.plot(x, accuracy, 'ro-', linewidth=2, markersize=8, label='Accuracy %')
                ax2.set_ylabel('Accuracy %', color='red')
                ax2.tick_params(axis='y', labelcolor='red')
                ax2.set_ylim(0, 100)
                
                plt.title('Model Version Performance')
                plt.xticks(x, versions, rotation=45)
                
                # Add legend
                lines1, labels1 = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['model_performance_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating model performance chart: {str(e)}")
        
        return charts
    
    def _generate_crop_monitoring_charts(self, report_data):
        """Generate charts for crop monitoring report."""
        charts = {}
        
        # 1. Diseases by crop type (grouped bar chart)
        if 'crop_diseases' in report_data and report_data['crop_diseases']:
            try:
                # Group by crop
                crop_disease_data = defaultdict(list)
                
                for item in report_data['crop_diseases']:
                    crop_disease_data[item['crop_name']].append({
                        'disease_name': item['disease_name'],
                        'count': item['count']
                    })
                
                # Get top crops by total disease count
                crop_totals = [(crop, sum(d['count'] for d in diseases)) 
                              for crop, diseases in crop_disease_data.items()]
                top_crops = [crop for crop, _ in sorted(crop_totals, key=lambda x: x[1], reverse=True)[:5]]
                
                plt.figure(figsize=(14, 8))
                
                # For each crop, show its top 3 diseases
                bar_width = 0.15
                index = np.arange(len(top_crops))
                
                for i, crop in enumerate(top_crops):
                    # Get top 3 diseases for this crop
                    top_diseases = sorted(crop_disease_data[crop], key=lambda x: x['count'], reverse=True)[:3]
                    
                    for j, disease in enumerate(top_diseases):
                        plt.bar(index[i] + j*bar_width, disease['count'], bar_width,
                               label=f"{crop} - {disease['disease_name']}" if i == 0 else disease['disease_name'])
                
                plt.xlabel('Crop')
                plt.ylabel('Number of Diagnoses')
                plt.title('Top Diseases by Crop Type')
                plt.xticks(index + bar_width, top_crops)
                plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['crop_diseases_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating crop diseases chart: {str(e)}")
        
        # 2. Seasonal disease patterns (heatmap)
        if 'seasonal_patterns' in report_data and report_data['seasonal_patterns']:
            try:
                # Group by month and disease
                seasonal_data = defaultdict(dict)
                all_months = set()
                all_diseases = set()
                
                for item in report_data['seasonal_patterns']:
                    month = item['month']
                    disease = item['disease_name']
                    count = item['count']
                    
                    all_months.add(month)
                    all_diseases.add(disease)
                    seasonal_data[disease][month] = count
                
                # Convert to matrix for heatmap
                months_list = sorted(all_months)
                diseases_list = sorted(all_diseases)
                
                data_matrix = np.zeros((len(diseases_list), len(months_list)))
                
                for i, disease in enumerate(diseases_list):
                    for j, month in enumerate(months_list):
                        data_matrix[i, j] = seasonal_data.get(disease, {}).get(month, 0)
                
                # Create heatmap
                plt.figure(figsize=(12, len(diseases_list) * 0.5 + 2))
                plt.imshow(data_matrix, cmap='YlOrRd', aspect='auto')
                
                # Add labels
                plt.yticks(np.arange(len(diseases_list)), diseases_list)
                plt.xticks(np.arange(len(months_list)), [calendar.month_abbr[m] for m in months_list])
                
                plt.colorbar(label='Number of Diagnoses')
                plt.title('Seasonal Disease Patterns')
                plt.xlabel('Month')
                plt.ylabel('Disease')
                
                # Add text annotations
                for i in range(len(diseases_list)):
                    for j in range(len(months_list)):
                        if data_matrix[i, j] > 0:
                            plt.text(j, i, int(data_matrix[i, j]), 
                                    ha='center', va='center', 
                                    color='black' if data_matrix[i, j] < np.max(data_matrix)/2 else 'white')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['seasonal_patterns_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating seasonal patterns chart: {str(e)}")
        
        return charts
    
    def _generate_geographical_insights_charts(self, report_data):
        """Generate charts for geographical insights report."""
        charts = {}
        
        # 1. Disease distribution by district (stacked bar chart)
        if 'district_distribution' in report_data and report_data['district_distribution']:
            try:
                # Group by district and province
                district_data = defaultdict(lambda: defaultdict(int))
                all_diseases = set()
                
                for item in report_data['district_distribution']:
                    district = f"{item['district_name']} ({item['province_name']})"
                    disease = item['disease_name']
                    count = item['count']
                    
                    district_data[district][disease] += count
                    all_diseases.add(disease)
                
                # Get top districts by total disease count
                district_totals = [(district, sum(counts.values())) 
                                for district, counts in district_data.items()]
                top_districts = [district for district, _ in sorted(district_totals, key=lambda x: x[1], reverse=True)[:10]]
                
                # Create stacked bar chart
                diseases_list = sorted(all_diseases)
                data_matrix = np.zeros((len(diseases_list), len(top_districts)))
                
                for i, disease in enumerate(diseases_list):
                    for j, district in enumerate(top_districts):
                        data_matrix[i, j] = district_data[district].get(disease, 0)
                
                # Plot stacked bars
                plt.figure(figsize=(14, 8))
                bottom = np.zeros(len(top_districts))
                
                for i, disease in enumerate(diseases_list):
                    plt.bar(top_districts, data_matrix[i], bottom=bottom, label=disease)
                    bottom += data_matrix[i]
                
                plt.xlabel('District')
                plt.ylabel('Number of Diagnoses')
                plt.title('Disease Distribution by District')
                plt.xticks(rotation=45, ha='right')
                plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['district_distribution_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating district distribution chart: {str(e)}")
        
        # 2. Districts with highest diagnosis activity (horizontal bar chart)
        if 'active_districts' in report_data and report_data['active_districts']:
            try:
                districts = [f"{item['district_name']} ({item['province_name']})" for item in report_data['active_districts']]
                counts = [item['diagnosis_count'] for item in report_data['active_districts']]
                
                plt.figure(figsize=(10, max(6, len(districts) * 0.4)))
                bars = plt.barh(districts, counts, color='lightgreen')
                plt.title('Districts with Highest Diagnosis Activity')
                plt.xlabel('Number of Diagnoses')
                plt.ylabel('District')
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    plt.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                            f'{width}', ha='left', va='center')
                
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                plt.close('all')
                
                charts['active_districts_chart'] = img_buffer
            except Exception as e:
                print(f"Error generating active districts chart: {str(e)}")
        
        return charts