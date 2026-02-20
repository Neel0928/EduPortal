from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.extensions import db
from app.models import Exam, Attendance, StudentProfile, Course
from datetime import datetime
from . import admin_bp


# --- Attendance Management ---
@admin_bp.route('/attendance')
@login_required
def attendance_list():
    # 1. Fetch Aggregated Counts via SQL
    # We need Total Days and Present Days per student
    from sqlalchemy import func, case
    
    # Query: StudentID, Total, Present
    stats = db.session.query(
        Attendance.student_id, 
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present')
    ).group_by(Attendance.student_id).all()
    
    stats_map = {s.student_id: {'total': s.total, 'present': s.present or 0} for s in stats}
    
    # 2. Fetch Students
    students = StudentProfile.query.all()
    
    summary = []
    for s in students:
        data = stats_map.get(s.id, {'total': 0, 'present': 0})
        total = data['total']
        present = data['present']
        pct = (present / total * 100) if total > 0 else 0
        
        summary.append({
            'name': s.display_name,
            'enrollment': s.enrollment_number,
            'batch': s.batch_year,
            'total': total,
            'present': present,
            'absent': total - present,
            'pct': round(pct, 1)
        })
        
    summary.sort(key=lambda x: x['pct']) # Show low attendance first? or Sort by name? Let's sort by Name.
    # summary.sort(key=lambda x: x['name']) # Uncomment if name sort preferred
    
    return render_template('attendance_list.html', summary=summary)

@admin_bp.route('/attendance/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    students = StudentProfile.query.all()
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        course_name = request.form.get('course_name')
        date_str = request.form.get('date')
        status = request.form.get('status')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            attendance = Attendance(
                student_id=student_id,
                course_name=course_name,
                date=date_obj,
                status=status
            )
            db.session.add(attendance)
            db.session.commit()
            flash('Attendance marked successfully!', 'success')
            return redirect(url_for('admin.attendance_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error marking attendance: {str(e)}', 'error')

    courses = Course.query.order_by(Course.code).all()
    return render_template('attendance_add.html', students=students, courses=courses)
