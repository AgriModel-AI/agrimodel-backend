from flask import jsonify, request, send_file
from flask_restful import Resource
from models import Comment, Community, Post, PostLike, Province, UserCommunity, db, Disease, DiagnosisResult, User, District
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

# ======== 1. Disease Cases Trend API ========
class DiseaseTrendResource(Resource):
    def get(self):
        """Get monthly distribution of disease cases"""
        # Default to last 12 months
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)
        
        # Parse query parameters if provided
        start_date_param = request.args.get('start_date')
        end_date_param = request.args.get('end_date')
        
        if start_date_param:
            start_date = datetime.strptime(start_date_param, '%Y-%m-%d')
        if end_date_param:
            end_date = datetime.strptime(end_date_param, '%Y-%m-%d')
        
        # Get monthly case counts
        monthly_data = (
            db.session.query(
                extract('year', DiagnosisResult.date).label('year'),
                extract('month', DiagnosisResult.date).label('month'),
                func.count(DiagnosisResult.resultId).label('case_count')
            )
            .filter(DiagnosisResult.date.between(start_date, end_date))
            .filter(DiagnosisResult.detected == True)
            .group_by('year', 'month')
            .order_by('year', 'month')
            .all()
        )
        
        # Format results
        trend_data = []
        for year, month, count in monthly_data:
            month_date = datetime(int(year), int(month), 1)
            trend_data.append({
                'month': month_date.strftime('%b %Y'),
                'count': count
            })
        
        return jsonify({
            'data': trend_data,
            'total_cases': sum(item['count'] for item in trend_data)
        })

# ======== 2. Disease Cases Summary API ========
class DiseaseSummaryResource(Resource):
    def get(self):
        """Get summary of diseases with case counts"""
        disease_summaries = (
            db.session.query(
                Disease.diseaseId,
                Disease.name,
                Disease.description,
                func.count(DiagnosisResult.resultId).label('total_cases')
            )
            .outerjoin(DiagnosisResult, Disease.diseaseId == DiagnosisResult.diseaseId)
            .filter(DiagnosisResult.detected == True)
            .group_by(Disease.diseaseId)
            .order_by(func.count(DiagnosisResult.resultId).desc())
            .all()
        )
        
        # Format results
        summary_data = []
        for disease_id, name, description, case_count in disease_summaries:
            summary_data.append({
                'disease_id': disease_id,
                'name': name,
                'description': description,
                'total_cases': case_count
            })
        
        # Include all diseases with zero cases if none found
        if not summary_data:
            diseases = Disease.query.all()
            summary_data = [{
                'disease_id': disease.diseaseId,
                'name': disease.name,
                'description': disease.description,
                'total_cases': 0
            } for disease in diseases]
        
        return jsonify({'data': summary_data})

# ======== 4. Recent Activity API ========
class RecentActivityResource(Resource):
    def get(self):
        """Get recent activities on the platform including community interactions"""
        limit = request.args.get('limit', 10, type=int)
        
        # Helper function to calculate time ago
        def format_time_ago(timestamp):
            time_diff = datetime.utcnow() - timestamp
            
            if time_diff.days > 1:
                return f"{time_diff.days} days ago"
            elif time_diff.total_seconds() >= 3600:
                hours = int(time_diff.total_seconds() / 3600)
                return f"{hours} hours ago"
            else:
                minutes = max(1, int(time_diff.total_seconds() / 60))
                return f"{minutes} minutes ago"
        
        all_activities = []
        
        # Get recent diagnosis submissions
        recent_diagnoses = (
            db.session.query(
                User.username,
                District.name.label('district'),
                DiagnosisResult.date,
                DiagnosisResult.detected,
                Disease.name.label('disease_name')
            )
            .join(User, DiagnosisResult.userId == User.userId)
            .join(District, DiagnosisResult.districtId == District.districtId)
            .join(Disease, DiagnosisResult.diseaseId == Disease.diseaseId, isouter=True)
            .order_by(DiagnosisResult.date.desc())
            .all()
        )
        
        # Format diagnosis results
        for username, district, date, detected, disease_name in recent_diagnoses:
            time_ago = format_time_ago(date)
            
            if detected and disease_name:
                message = f"New {disease_name} diagnosis submitted from {district}"
            else:
                message = f"New disease diagnosis submitted from {district}"
            
            all_activities.append({
                'type': 'diagnosis',
                'message': message,
                'user': username,
                'time': date.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': time_ago,
                'timestamp': date
            })
        
        # Get recent posts
        recent_posts = (
            db.session.query(
                User.username,
                Community.name.label('community_name'),
                Post.createdAt,
                Post.postId
            )
            .join(User, Post.userId == User.userId)
            .join(Community, Post.communityId == Community.communityId)
            .order_by(Post.createdAt.desc())
            .all()
        )
        
        # Format post activities
        for username, community_name, created_at, post_id in recent_posts:
            time_ago = format_time_ago(created_at)
            message = f"{username} posted in {community_name} community"
            
            all_activities.append({
                'type': 'post',
                'message': message,
                'user': username,
                'time': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': time_ago,
                'timestamp': created_at,
                'post_id': post_id
            })
        
        # Get recent comments
        recent_comments = (
            db.session.query(
                User.username,
                Post.postId,
                Community.name.label('community_name'),
                Comment.createdAt
            )
            .join(User, Comment.userId == User.userId)
            .join(Post, Comment.postId == Post.postId)
            .join(Community, Post.communityId == Community.communityId)
            .order_by(Comment.createdAt.desc())
            .all()
        )
        
        # Format comment activities
        for username, post_id, community_name, created_at in recent_comments:
            time_ago = format_time_ago(created_at)
            message = f"{username} commented on a post in {community_name} community"
            
            all_activities.append({
                'type': 'comment',
                'message': message,
                'user': username,
                'time': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': time_ago,
                'timestamp': created_at,
                'post_id': post_id
            })
        
        # Get recent likes
        recent_likes = (
            db.session.query(
                User.username,
                Post.postId,
                Community.name.label('community_name'),
                PostLike.createdAt
            )
            .join(User, PostLike.userId == User.userId)
            .join(Post, PostLike.postId == Post.postId)
            .join(Community, Post.communityId == Community.communityId)
            .order_by(PostLike.createdAt.desc())
            .all()
        )
        
        # Format like activities
        for username, post_id, community_name, created_at in recent_likes:
            time_ago = format_time_ago(created_at)
            message = f"{username} liked a post in {community_name} community"
            
            all_activities.append({
                'type': 'like',
                'message': message,
                'user': username,
                'time': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': time_ago,
                'timestamp': created_at,
                'post_id': post_id
            })
        
        # Get recent community joins
        recent_joins = (
            db.session.query(
                User.username,
                Community.name.label('community_name'),
                UserCommunity.joinedDate
            )
            .join(User, UserCommunity.userId == User.userId)
            .join(Community, UserCommunity.communityId == Community.communityId)
            .order_by(UserCommunity.joinedDate.desc())
            .all()
        )
        
        # Format community join activities
        for username, community_name, joined_date in recent_joins:
            time_ago = format_time_ago(joined_date)
            message = f"{username} joined the {community_name} community"
            
            all_activities.append({
                'type': 'join',
                'message': message,
                'user': username,
                'time': joined_date.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': time_ago,
                'timestamp': joined_date
            })
        
        # Sort all activities by timestamp (newest first) and limit results
        all_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        limited_activities = all_activities[:limit]
        
        # Remove the timestamp field from the output
        for activity in limited_activities:
            del activity['timestamp']
        
        return jsonify({'data': limited_activities})

# ======== 5. Province Diagnoses Summary API ========
class ProvinceDignosisSummaryResource(Resource):
    def get(self):
        """Get summary of diagnoses by province"""
        # Get count of cases per province
        province_summary = (
            db.session.query(
                func.coalesce(Province.name, 'Unknown').label('province_name'),
                func.count(DiagnosisResult.resultId).label('case_count')
            )
            .join(District, DiagnosisResult.districtId == District.districtId, isouter=True)
            .join(Province, District.provinceId == Province.provinceId, isouter=True)
            .filter(DiagnosisResult.detected == True)
            .group_by(Province.name)
            .order_by(Province.name)
            .all()
        )
        
        # Format results
        summary_data = [{
            'province': province_name,
            'cases': case_count
        } for province_name, case_count in province_summary]
        
        # Ensure all provinces are included, even with zero cases
        provinces = ['Northern Province', 'Southern Province', 'Eastern Province', 
                    'Western Province', 'Kigali City']
        existing = {item['province'] for item in summary_data}
        
        for province in provinces:
            if province not in existing:
                summary_data.append({
                    'province': province,
                    'cases': 0
                })
        
        # Sort by province name
        summary_data.sort(key=lambda x: x['province'])
        
        return jsonify({'data': summary_data})