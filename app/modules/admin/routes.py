from flask import render_template
from flask_login import login_required
from app.models import StudentProfile, FacultyProfile, Notice, User, Course
from app.extensions import db
from . import admin_bp
from sqlalchemy import func

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # 1. Counts
    total_students = StudentProfile.query.count()
    total_faculty = FacultyProfile.query.count()
    # Count distinct courses
    # distinct_courses = db.session.query(StudentProfile.course_name).distinct().count() 
    # Better: list of courses + count
    
    # 2. Pie Chart Data (Student vs Course)
    # result = [(course_name, count), ...]
    course_stats = db.session.query(
        StudentProfile.course_name, 
        func.count(StudentProfile.id)
    ).group_by(StudentProfile.course_name).all()
    
    # Process for Chart.js
    course_labels = [stat[0] for stat in course_stats]
    course_counts = [stat[1] for stat in course_stats]
    
    # True Total Courses
    total_courses = Course.query.count()

    # 3. Recent Activity (Latest Notices)
    recent_notices = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()

    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_faculty=total_faculty,
        total_courses=total_courses,
        course_labels=course_labels,
        course_counts=course_counts,
        recent_notices=recent_notices
    )

@admin_bp.route('/dashboard/system_report_print')
@login_required
def system_report_print():
    from datetime import datetime
    
    # 1. Gather Data
    total_students = StudentProfile.query.count()
    total_faculty = FacultyProfile.query.count()
    total_courses = Course.query.count()
    
    # Detailed stats
    courses = db.session.query(StudentProfile.course_name, func.count(StudentProfile.id)).group_by(StudentProfile.course_name).all()
    notices = Notice.query.order_by(Notice.created_at.desc()).limit(10).all()
    
    generated_at = datetime.now()
    
    return render_template(
        'reports/system_report_print.html',
        total_students=total_students,
        total_faculty=total_faculty,
        total_courses=total_courses,
        courses=courses,
        notices=notices,
        generated_at=generated_at
    )
