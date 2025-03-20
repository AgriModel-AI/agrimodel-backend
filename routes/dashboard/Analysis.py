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

# ======== 3. Reports API ========
class ReportsResource(Resource):
    def get(self, report_type):
        """Generate and download detailed reports"""
        if report_type == 'disease_prevalence':
            return self.disease_prevalence_report()
        elif report_type == 'client_activity':
            return self.client_activity_report()
        elif report_type == 'growth_analysis':
            return self.growth_analysis_report()
        else:
            return {"message": "Invalid report type"}, 400
    
    def disease_prevalence_report(self):
        """Detailed analysis by region and time"""
        format_type = request.args.get('format', 'json')
        region_id = request.args.get('region_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = (
            db.session.query(
                Disease.name.label('disease'),
                func.count(DiagnosisResult.resultId).label('cases'),
                District.name.label('district'),
                db.func.date_trunc('month', DiagnosisResult.date).label('month')
            )
            .join(Disease, DiagnosisResult.diseaseId == Disease.diseaseId)
            .join(District, DiagnosisResult.districtId == District.districtId)
            .filter(DiagnosisResult.detected == True)
        )
        
        # Apply filters
        if region_id:
            query = query.filter(District.provinceId == region_id)
        if start_date:
            query = query.filter(DiagnosisResult.date >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(DiagnosisResult.date <= datetime.strptime(end_date, '%Y-%m-%d'))
        
        results = (
            query.group_by('disease', 'district', 'month')
            .order_by('month', 'district', 'disease')
            .all()
        )
        
        # Format data
        report_data = [{
            'disease': disease,
            'cases': cases,
            'district': district,
            'month': month.strftime('%Y-%m') if month else None
        } for disease, cases, district, month in results]
        
        # Return in requested format
        return self._format_report(report_data, format_type, 'disease_prevalence_report')
    
    def client_activity_report(self):
        """User engagement and diagnosis trends"""
        format_type = request.args.get('format', 'json')
        
        # Get user activity data
        user_activity = (
            db.session.query(
                User.userId,
                User.username,
                func.count(DiagnosisResult.resultId).label('diagnosis_count'),
                func.max(DiagnosisResult.date).label('last_active')
            )
            .join(DiagnosisResult, User.userId == DiagnosisResult.userId)
            .group_by(User.userId)
            .order_by(func.count(DiagnosisResult.resultId).desc())
            .all()
        )
        
        # Format data
        report_data = [{
            'user_id': user_id,
            'username': username,
            'diagnosis_count': count,
            'last_active': last_active.strftime('%Y-%m-%d %H:%M:%S') if last_active else None
        } for user_id, username, count, last_active in user_activity]
        
        # Return in requested format
        return self._format_report(report_data, format_type, 'client_activity_report')
    
    def growth_analysis_report(self):
        """Month-over-month platform growth"""
        format_type = request.args.get('format', 'json')
        
        # Get monthly user signups and diagnoses
        user_growth = (
            db.session.query(
                extract('year', User.createdAt).label('year'),
                extract('month', User.createdAt).label('month'),
                func.count(User.userId).label('new_users')
            )
            .group_by('year', 'month')
            .order_by('year', 'month')
            .all()
        )
        
        diagnosis_growth = (
            db.session.query(
                extract('year', DiagnosisResult.date).label('year'),
                extract('month', DiagnosisResult.date).label('month'),
                func.count(DiagnosisResult.resultId).label('diagnosis_count')
            )
            .group_by('year', 'month')
            .order_by('year', 'month')
            .all()
        )
        
        # Combine data
        growth_data = {}
        
        for year, month, count in user_growth:
            month_key = f"{int(year)}-{int(month):02d}"
            if month_key not in growth_data:
                growth_data[month_key] = {
                    'new_users': 0, 
                    'diagnosis_count': 0, 
                    'month_label': f"{int(year)}-{int(month):02d}"
                }
            growth_data[month_key]['new_users'] = count
        
        for year, month, count in diagnosis_growth:
            month_key = f"{int(year)}-{int(month):02d}"
            if month_key not in growth_data:
                growth_data[month_key] = {
                    'new_users': 0, 
                    'diagnosis_count': 0, 
                    'month_label': f"{int(year)}-{int(month):02d}"
                }
            growth_data[month_key]['diagnosis_count'] = count
        
        # Calculate MoM growth
        report_data = list(growth_data.values())
        report_data.sort(key=lambda x: x['month_label'])
        
        for i in range(1, len(report_data)):
            prev = report_data[i-1]
            curr = report_data[i]
            
            # User growth %
            if prev['new_users'] > 0:
                user_growth_pct = ((curr['new_users'] - prev['new_users']) / prev['new_users']) * 100
            else:
                user_growth_pct = 0 if curr['new_users'] == 0 else 100
            
            # Diagnosis growth %
            if prev['diagnosis_count'] > 0:
                diag_growth_pct = ((curr['diagnosis_count'] - prev['diagnosis_count']) / prev['diagnosis_count']) * 100
            else:
                diag_growth_pct = 0 if curr['diagnosis_count'] == 0 else 100
            
            curr['user_growth_pct'] = round(user_growth_pct, 2)
            curr['diagnosis_growth_pct'] = round(diag_growth_pct, 2)
        
        # First month has no prior month for growth calculation
        if report_data:
            report_data[0]['user_growth_pct'] = 0
            report_data[0]['diagnosis_growth_pct'] = 0
        
        # Return in requested format
        return self._format_report(report_data, format_type, 'growth_analysis_report')
    
    def _format_report(self, data, format_type, filename):
        """Helper to return report in requested format"""
        if format_type == 'json':
            return jsonify({'data': data})
        elif format_type == 'csv':
            df = pd.DataFrame(data)
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            
            return send_file(
                csv_buffer,
                as_attachment=True,
                download_name=f'{filename}.csv',
                mimetype='text/csv'
            )
        elif format_type == 'excel':
            df = pd.DataFrame(data)
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            
            return send_file(
                excel_buffer,
                as_attachment=True,
                download_name=f'{filename}.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

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