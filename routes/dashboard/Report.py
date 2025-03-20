import io
from flask import make_response, request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
import xlsxwriter
from models import Province, db, Disease, DiagnosisResult, User, District
from sqlalchemy import and_, case, distinct, func, extract, or_
from datetime import datetime
import logging

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie


class ReportsResource(Resource):
    # Company brand colors
    COLORS = {
        'primary': '#1E8449',    # Green - main color
        'secondary': '#2874A6',  # Blue - secondary color
        'accent': '#F39C12',     # Orange - accent color
        'light': '#EBF5FB',      # Light blue - background
        'dark': '#212F3D',       # Dark blue - text
        'success': '#27AE60',    # Green - positive indicators
        'warning': '#F39C12',    # Orange - warning indicators
        'danger': '#C0392B',     # Red - negative indicators
        'chart_colors': ['#1E8449', '#2874A6', '#F39C12', '#8E44AD', '#2E86C1', '#28B463', '#D35400', '#CB4335']
    }
    
    # Company logo path
    LOGO_PATH = 'http://localhost:3000/assets/logoBlack.png'
    REPORT_TITLE = 'AgriModel Analytics'
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    # @jwt_required()
    def get(self, report_type):
        """
        Generate and download detailed reports with professional formatting
        
        Parameters:
            report_type (str): Type of report to generate
            
        Query Parameters:
            format (str): Output format - 'excel' or 'pdf' (default: 'pdf')
            start_date (str): Filter data from this date (YYYY-MM-DD)
            end_date (str): Filter data to this date (YYYY-MM-DD)
            region_id (int): Filter by province ID
            district_id (int): Filter by district ID
            
        Returns:
            Report file download in requested format
        """
        try:
            # Validate format type
            format_type = request.args.get('format', 'pdf').lower()
            if format_type not in ['pdf', 'excel']:
                return {"error": "Invalid format type. Please use 'pdf' or 'excel'"}, 400
                
            # Parse date parameters
            start_date, end_date = self._parse_date_params(
                request.args.get('start_date'), 
                request.args.get('end_date')
            )
            
            # Generate appropriate report
            if report_type == 'disease_prevalence':
                return self.disease_prevalence_report(format_type, start_date, end_date)
            elif report_type == 'client_activity':
                return self.client_activity_report(format_type, start_date, end_date)
            elif report_type == 'growth_analysis':
                return self.growth_analysis_report(format_type, start_date, end_date)
            elif report_type == 'regional_distribution':
                return self.regional_distribution_report(format_type, start_date, end_date)
            else:
                return {"error": "Invalid report type"}, 400
                
        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            return {"error": "Failed to generate report"}, 500
    
    def _parse_date_params(self, start_date_str, end_date_str):
        """Parse and validate date parameters"""
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Invalid start_date format. Use YYYY-MM-DD")
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # Set to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise ValueError("Invalid end_date format. Use YYYY-MM-DD")
                
        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date cannot be after end_date")
            
        return start_date, end_date
    
    def _apply_common_filters(self, query, start_date, end_date, date_field):
        """Apply common date filters to query"""
        if start_date:
            query = query.filter(date_field >= start_date)
        if end_date:
            query = query.filter(date_field <= end_date)
        return query
    
    def _format_report(self, data, format_type, report_title, filename_base):
        """Format report in requested output format with company branding"""
        current_date = datetime.now()
        timestamp = current_date.strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_base}_{timestamp}"
        
        # Date range text
        date_range = f"{data['summary']['report_period']['start_date']} to {data['summary']['report_period']['end_date']}"
        
        if format_type == 'excel':
            return self._generate_excel_report(data, report_title, date_range, filename)
        else:  # PDF is default
            return self._generate_pdf_report(data, report_title, date_range, filename)
    
    def _generate_excel_report(self, data, report_title, date_range, filename):
        """Generate a professionally formatted Excel report"""
        # Create Excel in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Define styles
        title_format = workbook.add_format({
            'bold': True, 
            'font_size': 18,
            'font_color': self.COLORS['dark'],
            'align': 'center',
            'valign': 'vcenter',
            'border': 0
        })
        
        subtitle_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'font_color': self.COLORS['secondary'],
            'align': 'center',
            'valign': 'vcenter',
            'border': 0
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': self.COLORS['primary'],
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        
        number_format = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0'
        })
        
        percent_format = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '0.00%'
        })
        
        date_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': 'yyyy-mm-dd'
        })
        
        section_format = workbook.add_format({
            'bold': True,
            'bg_color': self.COLORS['secondary'],
            'font_color': 'white',
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 12
        })
        
        highlight_format = workbook.add_format({
            'bold': True,
            'bg_color': self.COLORS['light'],
            'font_color': self.COLORS['dark'],
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 11
        })
        
        # Create Summary worksheet
        summary_sheet = workbook.add_worksheet('Summary')
        summary_sheet.set_column('A:A', 20)
        summary_sheet.set_column('B:B', 30)
        
        # Add logo if available
        try:
            summary_sheet.insert_image('A1', self.LOGO_PATH, {'x_scale': 0.5, 'y_scale': 0.5})
        except Exception:
            pass  # Continue if logo insertion fails
        
        # Add title and date
        summary_sheet.merge_range('C1:G1', report_title, title_format)
        summary_sheet.merge_range('C2:G2', date_range, subtitle_format)
        summary_sheet.merge_range('C3:G3', f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_format)
        
        # Add summary data based on report type
        if 'summary' in data:
            summary_sheet.merge_range('A5:G5', 'KEY METRICS', section_format)
            row = 6
            
            # Process different summary structures based on what's available
            if 'total_cases' in data['summary']:
                summary_sheet.write(row, 0, 'Total Cases:', highlight_format)
                summary_sheet.write(row, 1, data['summary']['total_cases'], number_format)
                row += 1
            
            if 'total_users' in data['summary']:
                summary_sheet.write(row, 0, 'Total Users:', highlight_format)
                summary_sheet.write(row, 1, data['summary']['total_users'], number_format)
                row += 1
                
                summary_sheet.write(row, 0, 'Active Users:', highlight_format)
                summary_sheet.write(row, 1, data['summary']['active_users'], number_format)
                row += 1
                
                summary_sheet.write(row, 0, 'Inactive Users:', highlight_format)
                summary_sheet.write(row, 1, data['summary']['inactive_users'], number_format)
                row += 1
                
                summary_sheet.write(row, 0, 'Total Diagnoses:', highlight_format)
                summary_sheet.write(row, 1, data['summary']['total_diagnoses'], number_format)
                row += 1
                
                summary_sheet.write(row, 0, 'Avg Diagnoses Per User:', highlight_format)
                summary_sheet.write(row, 1, data['summary']['avg_diagnoses_per_user'], number_format)
                row += 1
            
            if 'total_period' in data['summary']:
                summary_sheet.write(row, 0, 'New Users (Period):', highlight_format)
                summary_sheet.write(row, 1, data['summary']['total_period']['new_users'], number_format)
                row += 1
                
                summary_sheet.write(row, 0, 'Diagnoses (Period):', highlight_format)
                summary_sheet.write(row, 1, data['summary']['total_period']['diagnoses'], number_format)
                row += 1
                
                summary_sheet.write(row, 0, 'Positive Diagnoses:', highlight_format)
                summary_sheet.write(row, 1, data['summary']['total_period']['positive_diagnoses'], number_format)
                row += 1
                
                summary_sheet.write(row, 0, 'Avg Monthly New Users:', highlight_format)
                summary_sheet.write(row, 1, data['summary']['avg_monthly']['new_users'], number_format)
                row += 1
            
            if 'disease_breakdown' in data['summary']:
                row += 2
                summary_sheet.merge_range(f'A{row}:G{row}', 'DISEASE BREAKDOWN', section_format)
                row += 1
                summary_sheet.write(row, 0, 'Disease', header_format)
                summary_sheet.write(row, 1, 'Cases', header_format)
                summary_sheet.write(row, 2, 'Percentage', header_format)
                row += 1
                
                for item in data['summary']['disease_breakdown']:
                    summary_sheet.write(row, 0, item['disease'], cell_format)
                    summary_sheet.write(row, 1, item['cases'], number_format)
                    summary_sheet.write(row, 2, item['percentage'] / 100, percent_format)
                    row += 1
            
            if 'province_summary' in data:
                row += 2
                summary_sheet.merge_range(f'A{row}:G{row}', 'REGIONAL BREAKDOWN', section_format)
                row += 1
                summary_sheet.write(row, 0, 'Province', header_format)
                summary_sheet.write(row, 1, 'Total Cases', header_format)
                summary_sheet.write(row, 2, 'Top Diseases', header_format)
                row += 1
                
                for item in data['province_summary']:
                    summary_sheet.write(row, 0, item['province'], cell_format)
                    summary_sheet.write(row, 1, item['total_cases'], number_format)
                    top_diseases = ', '.join([f"{d['disease']} ({d['cases']})" for d in item['top_diseases']])
                    summary_sheet.write(row, 2, top_diseases, cell_format)
                    row += 1
        
        # Create Detailed Data worksheet
        if 'detailed_data' in data and data['detailed_data']:
            detailed_sheet = workbook.add_worksheet('Detailed Data')
            
            # Set column widths
            header_keys = list(data['detailed_data'][0].keys())
            for i, key in enumerate(header_keys):
                col_width = max(len(key) + 2, 15)
                detailed_sheet.set_column(i, i, col_width)
            
            # Add title
            detailed_sheet.merge_range(f'A1:{chr(65 + len(header_keys) - 1)}1', f"{report_title} - Detailed Data", title_format)
            detailed_sheet.merge_range(f'A2:{chr(65 + len(header_keys) - 1)}2', date_range, subtitle_format)
            
            # Add headers
            row = 3
            for col, header in enumerate(header_keys):
                formatted_header = header.replace('_', ' ').title()
                detailed_sheet.write(row, col, formatted_header, header_format)
            
            # Add data
            row += 1
            for item in data['detailed_data']:
                for col, key in enumerate(header_keys):
                    value = item[key]
                    
                    # Apply appropriate formatting based on data type
                    if isinstance(value, (int, float)) and not isinstance(value, bool) and 'date' not in key and 'id' not in key:
                        detailed_sheet.write(row, col, value, number_format)
                    elif isinstance(value, datetime) or ('date' in key and value):
                        detailed_sheet.write(row, col, value, date_format)
                    elif isinstance(value, (int, float)) and ('id' in key):
                        detailed_sheet.write(row, col, value, cell_format)
                    elif isinstance(value, bool):
                        detailed_sheet.write(row, col, 'Yes' if value else 'No', cell_format)
                    elif value is None:
                        detailed_sheet.write(row, col, '', cell_format)
                    else:
                        detailed_sheet.write(row, col, value, cell_format)
                row += 1
        
        # Create Monthly Trends worksheet if applicable
        if 'monthly_data' in data and data['monthly_data']:
            trends_sheet = workbook.add_worksheet('Monthly Trends')
            
            # Set column widths
            header_keys = list(data['monthly_data'][0].keys())
            for i, key in enumerate(header_keys):
                col_width = max(len(key) + 2, 15)
                trends_sheet.set_column(i, i, col_width)
            
            # Add title
            trends_sheet.merge_range(f'A1:{chr(65 + len(header_keys) - 1)}1', f"{report_title} - Monthly Trends", title_format)
            trends_sheet.merge_range(f'A2:{chr(65 + len(header_keys) - 1)}2', date_range, subtitle_format)
            
            # Add headers
            row = 3
            for col, header in enumerate(header_keys):
                formatted_header = header.replace('_', ' ').title()
                trends_sheet.write(row, col, formatted_header, header_format)
            
            # Add data
            row += 1
            for item in data['monthly_data']:
                for col, key in enumerate(header_keys):
                    value = item[key]
                    
                    # Apply appropriate formatting based on data type
                    if key.endswith('_pct'):
                        trends_sheet.write(row, col, value / 100, percent_format)
                    elif isinstance(value, (int, float)) and not isinstance(value, bool):
                        trends_sheet.write(row, col, value, number_format)
                    else:
                        trends_sheet.write(row, col, value, cell_format)
                row += 1
            
            # Add chart for monthly trends
            chart = workbook.add_chart({'type': 'line'})
            
            # Set up the data series
            chart.add_series({
                'name': 'New Users',
                'categories': f'=Monthly Trends!$A$5:$A${4 + len(data["monthly_data"])}',
                'values': f'=Monthly Trends!$B$5:$B${4 + len(data["monthly_data"])}',
                'line': {'color': self.COLORS['primary'], 'width': 2.25},
                'marker': {'type': 'circle', 'size': 4}
            })
            
            chart.add_series({
                'name': 'Diagnoses',
                'categories': f'=Monthly Trends!$A$5:$A${4 + len(data["monthly_data"])}',
                'values': f'=Monthly Trends!$C$5:$C${4 + len(data["monthly_data"])}',
                'line': {'color': self.COLORS['secondary'], 'width': 2.25},
                'marker': {'type': 'square', 'size': 4}
            })
            
            # Configure chart
            chart.set_title({'name': 'Monthly Growth Trends', 'name_font': {'size': 14, 'bold': True}})
            chart.set_x_axis({'name': 'Month', 'name_font': {'size': 10, 'bold': True}})
            chart.set_y_axis({'name': 'Count', 'name_font': {'size': 10, 'bold': True}})
            chart.set_legend({'position': 'bottom'})
            chart.set_size({'width': 720, 'height': 400})
            
            # Insert chart
            trends_sheet.insert_chart(f'A{7 + len(data["monthly_data"])}', chart)
        
        workbook.close()
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response
        
    def disease_prevalence_report(self, format_type, start_date, end_date):
        """
        Generate detailed analysis of disease prevalence by region and time
        """
        # Get filter parameters
        region_id = request.args.get('region_id', type=int)
        district_id = request.args.get('district_id', type=int)
        limit = min(int(request.args.get('limit', 1000)), 5000)  # Cap at 5000 records
        
        # Build base query
        query = (
            db.session.query(
                Disease.name.label('disease'),
                func.count(DiagnosisResult.resultId).label('cases'),
                District.name.label('district'),
                Province.name.label('province'),
                db.func.date_trunc('month', DiagnosisResult.date).label('month')
            )
            .join(Disease, DiagnosisResult.diseaseId == Disease.diseaseId)
            .join(District, DiagnosisResult.districtId == District.districtId)
            .join(Province, District.provinceId == Province.provinceId)
            .filter(DiagnosisResult.detected == True)
        )
        
        # Apply filters
        query = self._apply_common_filters(query, start_date, end_date, DiagnosisResult.date)
        
        if region_id:
            query = query.filter(District.provinceId == region_id)
        if district_id:
            query = query.filter(DiagnosisResult.districtId == district_id)
        
        # Execute query with grouping
        results = (
            query.group_by(Disease.name, District.name, Province.name, 'month')
            .order_by('month', Province.name, District.name, Disease.name)
            .limit(limit)
            .all()
        )
        
        # Format data
        report_data = [{
            'disease': disease,
            'cases': cases,
            'district': district,
            'province': province,
            'month': month.strftime('%Y-%m') if month else None
        } for disease, cases, district, province, month in results]
        
        # Calculate totals and percentages
        total_cases = sum(item['cases'] for item in report_data) if report_data else 0
        disease_totals = {}
        province_totals = {}
        
        for item in report_data:
            # Disease totals
            disease = item['disease']
            if disease not in disease_totals:
                disease_totals[disease] = 0
            disease_totals[disease] += item['cases']
            
            # Province totals
            province = item['province']
            if province not in province_totals:
                province_totals[province] = {
                    'total': 0,
                    'diseases': {}
                }
            province_totals[province]['total'] += item['cases']
            
            if disease not in province_totals[province]['diseases']:
                province_totals[province]['diseases'][disease] = 0
            province_totals[province]['diseases'][disease] += item['cases']
        
        # Format province data for the report
        province_summary = []
        for province, data in province_totals.items():
            top_diseases = [
                {'disease': disease, 'cases': cases}
                for disease, cases in sorted(data['diseases'].items(), key=lambda x: x[1], reverse=True)
            ][:3]  # Top 3 diseases
            
            province_summary.append({
                'province': province,
                'total_cases': data['total'],
                'percentage': round((data['total'] / total_cases * 100), 2) if total_cases > 0 else 0,
                'top_diseases': top_diseases
            })
        
        # Sort provinces by total cases
        province_summary.sort(key=lambda x: x['total_cases'], reverse=True)
        
        # Create summary
        summary = {
            'total_cases': total_cases,
            'disease_breakdown': [
                {'disease': disease, 'cases': cases, 'percentage': round((cases/total_cases)*100, 2) if total_cases > 0 else 0}
                for disease, cases in sorted(disease_totals.items(), key=lambda x: x[1], reverse=True)
            ],
            'report_period': {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else 'All time',
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else 'Present'
            }
        }
        
        # Return formatted report
        return self._format_report({
            'summary': summary,
            'province_summary': province_summary,
            'detailed_data': report_data
        }, format_type, "Plant Disease Prevalence Report", 'disease_prevalence_report')
    
    def client_activity_report(self, format_type, start_date, end_date):
        """
        Generate detailed analysis of user engagement and diagnosis trends
        """
        # Get filter parameters
        limit = min(int(request.args.get('limit', 1000)), 5000)  # Cap at 5000 records
        
        # Get user activity data
        user_activity_query = (
            db.session.query(
                User.userId,
                User.username,
                User.email,
                User.createdAt.label('joined_date'),
                func.count(DiagnosisResult.resultId).label('diagnosis_count'),
                func.max(DiagnosisResult.date).label('last_active'),
                func.min(DiagnosisResult.date).label('first_diagnosis'),
                func.count(distinct(DiagnosisResult.diseaseId)).label('unique_diseases'),
                func.sum(case((DiagnosisResult.detected == True, 1), else_=0)).label('positive_diagnoses')
            )
            .outerjoin(DiagnosisResult, User.userId == DiagnosisResult.userId)
            .group_by(User.userId)
        )
        
        # Apply filters
        if start_date or end_date:
            user_activity_query = user_activity_query.having(
                or_(
                    func.max(DiagnosisResult.date).is_(None),
                    and_(
                        func.max(DiagnosisResult.date) >= start_date if start_date else True,
                        func.max(DiagnosisResult.date) <= end_date if end_date else True
                    )
                )
            )
        
        # Execute query
        user_activity = (
            user_activity_query
            .order_by(func.count(DiagnosisResult.resultId).desc())
            .limit(limit)
            .all()
        )
        
        # Format data
        report_data = [{
            'user_id': user_id,
            'username': username,
            'email': email,
            'joined_date': joined_date,
            'diagnosis_count': diagnosis_count,
            'last_active': last_active,
            'first_diagnosis': first_diagnosis,
            'unique_diseases': unique_diseases,
            'positive_diagnoses': positive_diagnoses,
            'positive_rate': round((positive_diagnoses / diagnosis_count * 100), 2) if diagnosis_count > 0 else 0
        } for user_id, username, email, joined_date, diagnosis_count, last_active, 
            first_diagnosis, unique_diseases, positive_diagnoses in user_activity]
        
        # Add usage statistics
        total_users = len(report_data)
        active_users = sum(1 for item in report_data if item['diagnosis_count'] > 0)
        total_diagnoses = sum(item['diagnosis_count'] for item in report_data)
        positive_diagnoses = sum(item['positive_diagnoses'] for item in report_data)
        
        summary = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'total_diagnoses': total_diagnoses,
            'positive_diagnoses': positive_diagnoses,
            'positive_rate': round((positive_diagnoses / total_diagnoses * 100), 2) if total_diagnoses > 0 else 0,
            'avg_diagnoses_per_user': round(total_diagnoses / active_users, 2) if active_users > 0 else 0,
            'report_period': {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else 'All time',
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else 'Present'
            }
        }
        
        # Return formatted report
        return self._format_report({
            'summary': summary,
            'detailed_data': report_data
        }, format_type, "User Activity Report", 'client_activity_report')
    
    def growth_analysis_report(self, format_type, start_date, end_date):
        """
        Generate detailed analysis of month-over-month platform growth
        """
        # Build date filters
        date_filter = []
        if start_date:
            date_filter.append(User.createdAt >= start_date)
            date_filter.append(DiagnosisResult.date >= start_date)
        if end_date:
            date_filter.append(User.createdAt <= end_date)
            date_filter.append(DiagnosisResult.date <= end_date)
        
        # Get monthly user signups
        user_growth = (
            db.session.query(
                extract('year', User.createdAt).label('year'),
                extract('month', User.createdAt).label('month'),
                func.count(User.userId).label('new_users')
            )
            .filter(*[f for f in date_filter if 'User' in str(f)])
            .group_by('year', 'month')
            .order_by('year', 'month')
            .all()
        )
        
        # Get monthly diagnoses
        diagnosis_growth = (
            db.session.query(
                extract('year', DiagnosisResult.date).label('year'),
                extract('month', DiagnosisResult.date).label('month'),
                func.count(DiagnosisResult.resultId).label('diagnosis_count'),
                func.count(distinct(DiagnosisResult.userId)).label('active_users')
            )
            .filter(*[f for f in date_filter if 'DiagnosisResult' in str(f)])
            .group_by('year', 'month')
            .order_by('year', 'month')
            .all()
        )
        
        # Get monthly positive diagnoses
        positive_diagnosis_growth = (
            db.session.query(
                extract('year', DiagnosisResult.date).label('year'),
                extract('month', DiagnosisResult.date).label('month'),
                func.count(DiagnosisResult.resultId).label('positive_count')
            )
            .filter(DiagnosisResult.detected == True)
            .filter(*[f for f in date_filter if 'DiagnosisResult' in str(f)])
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
                    'active_users': 0,
                    'positive_count': 0,
                    'month_label': f"{int(year)}-{int(month):02d}"
                }
            growth_data[month_key]['new_users'] = count
        
        for year, month, count, active_users in diagnosis_growth:
            month_key = f"{int(year)}-{int(month):02d}"
            if month_key not in growth_data:
                growth_data[month_key] = {
                    'new_users': 0, 
                    'diagnosis_count': 0,
                    'active_users': 0,
                    'positive_count': 0,
                    'month_label': f"{int(year)}-{int(month):02d}"
                }
            growth_data[month_key]['diagnosis_count'] = count
            growth_data[month_key]['active_users'] = active_users
        
        for year, month, count in positive_diagnosis_growth:
            month_key = f"{int(year)}-{int(month):02d}"
            if month_key not in growth_data:
                growth_data[month_key] = {
                    'new_users': 0, 
                    'diagnosis_count': 0,
                    'active_users': 0,
                    'positive_count': 0,
                    'month_label': f"{int(year)}-{int(month):02d}"
                }
            growth_data[month_key]['positive_count'] = count
        
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
            
            # Active users growth %
            if prev['active_users'] > 0:
                active_users_growth_pct = ((curr['active_users'] - prev['active_users']) / prev['active_users']) * 100
            else:
                active_users_growth_pct = 0 if curr['active_users'] == 0 else 100
            
            curr['user_growth_pct'] = round(user_growth_pct, 2)
            curr['diagnosis_growth_pct'] = round(diag_growth_pct, 2)
            curr['active_users_growth_pct'] = round(active_users_growth_pct, 2)
            
            # Calculate positive rate
            if curr['diagnosis_count'] > 0:
                curr['positive_rate'] = round((curr['positive_count'] / curr['diagnosis_count']) * 100, 2)
            else:
                curr['positive_rate'] = 0
        
        # Calculate cumulative growth
        cumulative_users = 0
        for item in report_data:
            cumulative_users += item['new_users']
            item['cumulative_users'] = cumulative_users
        
        # Add summary statistics
        summary = {
            'total_period': {
                'new_users': sum(item['new_users'] for item in report_data),
                'diagnoses': sum(item['diagnosis_count'] for item in report_data),
                'positive_diagnoses': sum(item['positive_count'] for item in report_data)
            },
            'avg_monthly': {
                'new_users': round(sum(item['new_users'] for item in report_data) / len(report_data), 2) if report_data else 0,
                'diagnoses': round(sum(item['diagnosis_count'] for item in report_data) / len(report_data), 2) if report_data else 0,
                'active_users': round(sum(item['active_users'] for item in report_data) / len(report_data), 2) if report_data else 0
            },
            'report_period': {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else 'All time',
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else 'Present'
            }
        }
        
        # Return formatted report
        return self._format_report({
            'summary': summary,
            'monthly_data': report_data
        }, format_type, "Platform Growth Analysis Report", 'growth_analysis_report')
    
    def regional_distribution_report(self, format_type, start_date, end_date):
        """
        Generate detailed analysis of disease distribution by region
        """
        # Get filter parameters
        region_id = request.args.get('region_id', type=int)
        limit = min(int(request.args.get('limit', 1000)), 5000)  # Cap at 5000 records
        
        # Build query
        query = (
            db.session.query(
                Province.name.label('province'),
                District.name.label('district'),
                Disease.name.label('disease'),
                func.count(DiagnosisResult.resultId).label('cases')
            )
            .join(District, DiagnosisResult.districtId == District.districtId)
            .join(Province, District.provinceId == Province.provinceId)
            .join(Disease, DiagnosisResult.diseaseId == Disease.diseaseId)
            .filter(DiagnosisResult.detected == True)
        )
        
        # Apply filters
        query = self._apply_common_filters(query, start_date, end_date, DiagnosisResult.date)
        
        if region_id:
            query = query.filter(Province.provinceId == region_id)
        
        # Execute query
        results = (
            query.group_by(Province.name, District.name, Disease.name)
            .order_by(Province.name, District.name, func.count(DiagnosisResult.resultId).desc())
            .limit(limit)
            .all()
        )
        
        # Format data
        report_data = [{
            'province': province,
            'district': district,
            'disease': disease,
            'cases': cases
        } for province, district, disease, cases in results]
        
        # Calculate totals
        total_cases = sum(item['cases'] for item in report_data) if report_data else 0
        
        # Group by province for summary
        province_summary = {}
        for item in report_data:
            province = item['province']
            cases = item['cases']
            
            if province not in province_summary:
                province_summary[province] = {'total_cases': 0, 'diseases': {}}
            
            province_summary[province]['total_cases'] += cases
            
            disease = item['disease']
            if disease not in province_summary[province]['diseases']:
                province_summary[province]['diseases'][disease] = 0
            province_summary[province]['diseases'][disease] += cases
        
        # Format province summary for report
        province_analysis = []
        for province, data in province_summary.items():
            top_diseases = sorted(
                [{'disease': d, 'cases': c} for d, c in data['diseases'].items()],
                key=lambda x: x['cases'],
                reverse=True
            )[:3]  # Top 3 diseases
            
            province_analysis.append({
                'province': province,
                'total_cases': data['total_cases'],
                'percentage': round((data['total_cases'] / total_cases * 100), 2) if total_cases > 0 else 0,
                'top_diseases': top_diseases
            })
        
        # Sort provinces by total cases
        province_analysis.sort(key=lambda x: x['total_cases'], reverse=True)
        
        # Create summary
        summary = {
            'total_cases': total_cases,
            'provinces_count': len(province_analysis),
            'report_period': {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else 'All time',
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else 'Present'
            }
        }
        
        # Return formatted report
        return self._format_report({
            'summary': summary,
            'province_summary': province_analysis,
            'detailed_data': report_data
        }, format_type, "Regional Disease Distribution Report", 'regional_distribution_report')
    
    def _generate_pdf_report(self, data, report_title, date_range, filename):
        """
        Generate a professionally formatted PDF report
        
        Args:
            data (dict): Report data including summary, disease_breakdown, etc.
            report_title (str): Title for the report
            date_range (str): Period covered by the report
            filename (str): Name for the output file (without extension)
            
        Returns:
            Flask response with PDF attachment
        """
    
        
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Set up document
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            # Get styles
            styles = self._create_styles()
            
            # Build the PDF content
            elements = []
            
            # Add header (logo and title)
            self._add_header(elements, styles, report_title, date_range)
            
            # Add summary section if data available
            if self._safe_get(data, 'summary'):
                self._add_summary_section(elements, styles, data)
            
            # Add disease breakdown if available
            if self._safe_get(data, 'summary', 'disease_breakdown'):
                self._add_disease_section(elements, styles, data)
            
            # Add province summary if available
            if self._safe_get(data, 'province_summary'):
                self._add_regional_section(elements, styles, data)
            
            # Add growth trend chart if available
            if self._safe_get(data, 'monthly_data') and len(data['monthly_data']) > 0:
                self._add_trends_section(elements, styles, data)
            
            # Add detailed data table (limited to first 20 records)
            if self._safe_get(data, 'detailed_data') and data['detailed_data']:
                self._add_details_section(elements, styles, data)
            
            # Add footer note
            self._add_footer(elements, styles)
            
            # Build the document
            doc.build(elements)
            buffer.seek(0)
            
            # Create response
            response = make_response(buffer.getvalue())
            response.headers['Content-Disposition'] = f'attachment; filename={filename}.pdf'
            response.headers['Content-type'] = 'application/pdf'
            return response
        
        except Exception as e:
            print('--------------------------------------')
            self.logger.error(f"Failed to generate PDF report: {str(e)}", exc_info=True)
            return {"error": f"Failed to generate report: {str(e)}"}
    
    def _create_styles(self):
        """Create and return document styles"""
        styles = getSampleStyleSheet()
        
        # Create custom styles
        # styles.add(ParagraphStyle(
        #     name='Title',
        #     parent=styles['Heading1'],
        #     fontSize=18,
        #     textColor=colors.HexColor(self.COLORS['dark']),
        #     alignment=1  # Center
        # ))
        
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(self.COLORS['secondary']),
            alignment=1  # Center
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.white,
            backgroundColor=colors.HexColor(self.COLORS['primary']),
            borderPadding=6,
            alignment=0  # Left
        ))
        
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=1  # Center
        ))
        
        return styles
    
    def _add_header(self, elements, styles, report_title, date_range):
        """Add logo and title section to the report"""
        # Add logo if available
        try:
            logo = Image(self.LOGO_PATH, width=1.5*inch, height=0.75*inch)
            elements.append(logo)
        except Exception as e:
            self.logger.warning(f"Could not load logo: {str(e)}")
            # Continue without logo
        
        # Add title and date
        elements.append(Paragraph(report_title, styles['Title']))
        elements.append(Paragraph(date_range, styles['Subtitle']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Subtitle']))
        elements.append(Spacer(1, 0.25*inch))
    
    def _add_summary_section(self, elements, styles, data):
        """Add key metrics summary section"""
        elements.append(Paragraph("KEY METRICS", styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        summary = data.get('summary', {})
        summary_data = []
        
        # Add total cases if available
        if 'total_cases' in summary:
            summary_data.append(['Total Cases:', f"{summary['total_cases']:,}"])
        
        # Add user metrics if available
        if 'total_users' in summary:
            summary_data.append(['Total Users:', f"{summary['total_users']:,}"])
            summary_data.append(['Active Users:', f"{summary['active_users']:,}"])
            summary_data.append(['Inactive Users:', f"{summary['inactive_users']:,}"])
            summary_data.append(['Total Diagnoses:', f"{summary['total_diagnoses']:,}"])
            summary_data.append(['Avg Diagnoses Per User:', f"{summary['avg_diagnoses_per_user']:,.2f}"])
        
        # Add period metrics if available
        if self._safe_get(summary, 'total_period'):
            summary_data.append(['New Users (Period):', f"{summary['total_period']['new_users']:,}"])
            summary_data.append(['Diagnoses (Period):', f"{summary['total_period']['diagnoses']:,}"])
            summary_data.append(['Positive Diagnoses:', f"{summary['total_period']['positive_diagnoses']:,}"])
        
        if self._safe_get(summary, 'avg_monthly'):
            summary_data.append(['Avg Monthly New Users:', f"{summary['avg_monthly']['new_users']:,.2f}"])
        
        if summary_data:
            summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.COLORS['light'])),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(self.COLORS['dark'])),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.2*inch))
    
    def _add_disease_section(self, elements, styles, data):
        """Add disease breakdown section with table and chart"""
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("DISEASE BREAKDOWN", styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        disease_breakdown = data['summary']['disease_breakdown']
        
        # Create table for disease breakdown
        disease_headers = ['Disease', 'Cases', 'Percentage']
        disease_data = [disease_headers]
        
        for item in disease_breakdown:
            disease_data.append([
                item.get('disease', 'Unknown'),
                f"{item.get('cases', 0):,}",
                f"{item.get('percentage', 0):.2f}%"
            ])
        
        disease_table = Table(disease_data, colWidths=[3*inch, 1*inch, 1*inch])
        disease_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(disease_table)
        
        # Add pie chart for disease distribution (top 5)
        if len(disease_breakdown) > 0:
            try:
                drawing = Drawing(400, 200)
                pie = Pie()
                pie.x = 100
                pie.y = 0
                pie.width = 150
                pie.height = 150
                
                # Take up to 5 diseases for the pie chart
                top_diseases = disease_breakdown[:5]
                pie.data = [item.get('cases', 0) for item in top_diseases]
                pie.labels = [item.get('disease', 'Unknown') for item in top_diseases]
                
                # Set colors
                pie.slices.strokeWidth = 0.5
                
                # Use a subset of chart colors
                chart_colors = [colors.HexColor(c) for c in self.COLORS['chart_colors']]
                for i, color in enumerate(chart_colors[:len(top_diseases)]):
                    pie.slices[i].fillColor = color
                
                drawing.add(pie)
                elements.append(drawing)
            except Exception as e:
                self.logger.warning(f"Failed to create pie chart: {str(e)}")
                # Continue without chart
        
        elements.append(Spacer(1, 0.2*inch))
    
    def _add_regional_section(self, elements, styles, data):
        """Add regional breakdown section"""
        elements.append(Paragraph("REGIONAL BREAKDOWN", styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        province_summary = data['province_summary']
        
        # Create table for province data
        province_headers = ['Province', 'Total Cases', 'Top Diseases']
        province_data = [province_headers]
        
        for item in province_summary:
            # Safely get top diseases
            top_diseases = item.get('top_diseases', [])
            diseases_str = ', '.join([
                f"{d.get('disease', 'Unknown')} ({d.get('cases', 0)})" 
                for d in top_diseases
            ])
            
            province_data.append([
                item.get('province', 'Unknown'),
                f"{item.get('total_cases', 0):,}",
                diseases_str
            ])
        
        province_table = Table(province_data, colWidths=[1.5*inch, 1*inch, 3*inch])
        province_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(province_table)
        elements.append(Spacer(1, 0.2*inch))
    
    def _add_trends_section(self, elements, styles, data):
        """Add monthly growth trends section with chart"""
        elements.append(Paragraph("MONTHLY GROWTH TRENDS", styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        monthly_data = data['monthly_data']
        
        try:
            # Create bar chart
            drawing = Drawing(500, 250)
            chart = VerticalBarChart()
            chart.x = 50
            chart.y = 50
            chart.height = 150
            chart.width = 400
            
            # Extract data safely
            new_users = [item.get('new_users', 0) for item in monthly_data]
            diagnosis_count = [item.get('diagnosis_count', 0) for item in monthly_data]
            
            chart.data = [new_users, diagnosis_count]
            chart.bars[0].fillColor = colors.HexColor(self.COLORS['primary'])
            chart.bars[1].fillColor = colors.HexColor(self.COLORS['secondary'])
            chart.valueAxis.valueMin = 0
            
            # Get month labels safely
            month_labels = [item.get('month_label', '') for item in monthly_data]
            chart.categoryAxis.categoryNames = month_labels
            chart.categoryAxis.labels.boxAnchor = 'ne'
            chart.categoryAxis.labels.angle = 30
            chart.categoryAxis.labels.dx = -8
            chart.categoryAxis.labels.dy = -2
            
            drawing.add(chart)
            elements.append(drawing)
            elements.append(Spacer(1, 0.1*inch))
            
            # Add legend table
            legend_data = [['', 'Month', 'New Users', 'Diagnoses']]
            for item in monthly_data:
                legend_data.append([
                    '',
                    item.get('month_label', ''),
                    f"{item.get('new_users', 0):,}",
                    f"{item.get('diagnosis_count', 0):,}"
                ])
            
            legend_table = Table(legend_data, colWidths=[0.2*inch, 1*inch, 1*inch, 1*inch])
            legend_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS['primary'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('GRID', (1, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                # Color the first column based on the chart colors
                ('BACKGROUND', (0, 1), (0, 1), colors.HexColor(self.COLORS['primary'])),
                ('BACKGROUND', (0, 2), (0, -1), colors.HexColor(self.COLORS['secondary']))
            ]))
            elements.append(legend_table)
        except Exception as e:
            self.logger.warning(f"Failed to create trends chart: {str(e)}")
            # Continue without chart
    
    def _add_details_section(self, elements, styles, data):
        """Add detailed data section (limited to top 20 records)"""
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("DETAILED DATA (TOP 20 RECORDS)", styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        detailed_data = data['detailed_data']
        
        try:
            # Ensure we have valid data
            if not detailed_data or not isinstance(detailed_data, list) or not detailed_data[0]:
                raise ValueError("Invalid detailed data format")
            
            # Create table headers
            headers = [key.replace('_', ' ').title() for key in detailed_data[0].keys()]
            
            # Only include essential columns to fit on the page
            filtered_headers = headers
            filtered_indices = list(range(len(headers)))
            
            if len(headers) > 5:
                # Prioritize the most important columns
                important_prefixes = ['disease', 'province', 'district', 'cases', 'date', 'month', 'user']
                filtered_headers = []
                filtered_indices = []
                
                for i, header in enumerate(headers):
                    if any(prefix in header.lower() for prefix in important_prefixes):
                        filtered_headers.append(header)
                        filtered_indices.append(i)
                
                # If still too many, limit to 5
                if len(filtered_headers) > 5:
                    filtered_headers = filtered_headers[:5]
                    filtered_indices = filtered_indices[:5]
            
            # Create table data
            table_data = [filtered_headers]
            
            # Add rows (limit to 20)
            for item in detailed_data[:20]:
                values = list(item.values())
                
                # Filter values to match headers if needed
                if len(filtered_headers) < len(values):
                    filtered_values = [values[i] for i in filtered_indices]
                    values = filtered_values
                
                # Format each value appropriately
                formatted_row = []
                for value in values:
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        formatted_row.append(f"{value:,}")
                    elif isinstance(value, datetime):
                        formatted_row.append(value.strftime('%Y-%m-%d'))
                    elif value is None:
                        formatted_row.append('')
                    else:
                        formatted_row.append(str(value))
                
                table_data.append(formatted_row)
            
            # Calculate column widths
            col_widths = [max(1*inch, 4.5*inch / len(filtered_headers))] * len(filtered_headers)
            
            # Create table
            detailed_table = Table(table_data, colWidths=col_widths)
            detailed_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS['primary'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # Smaller font to fit more data
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(detailed_table)
        except Exception as e:
            self.logger.warning(f"Failed to create detailed data table: {str(e)}")
            elements.append(Paragraph("Unable to display detailed data: " + str(e), styles['Normal']))
    
    def _add_footer(self, elements, styles):
        """Add footer with copyright and contact information"""
        elements.append(Spacer(1, 0.5*inch))
        footer_text = f"This report was generated automatically by {self.REPORT_TITLE} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. For questions or support, please contact support@agrimodel.com"
        elements.append(Paragraph(footer_text, styles['Footer']))
    
    def _safe_get(self, dict_obj, *keys):
        """Safely navigate nested dictionaries"""
        if not dict_obj or not isinstance(dict_obj, dict):
            return None
        
        temp = dict_obj
        for key in keys:
            if not isinstance(temp, dict) or key not in temp:
                return None
            temp = temp[key]
        return temp