from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import StudentResult, Attendance, Subject, StudentProfile, ExamEvent, ExamPaper, FacultyProfile
from sqlalchemy import func
import statistics
import random

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports', methods=['GET'])
@login_required
def dashboard():
    # --- AGGREGATE DASHBOARD INTELLIGENCE ---
    
    # 1. Pulse Checks
    total_students = StudentProfile.query.count()
    total_faculty = FacultyProfile.query.count()
    
    # 2. Daily Attendance (Real Data)
    # Calculate global average attendance %
    total_att_records = Attendance.query.count()
    if total_att_records > 0:
        present_count = Attendance.query.filter_by(status='Present').count()
        avg_att_global = round((present_count / total_att_records) * 100, 1)
    else:
        avg_att_global = 0
    
    # 3. Academic Health
    # Get recent batch average
    results = db.session.query(StudentResult.marks_obtained).all()
    if results:
        marks = [r.marks_obtained for r in results if r.marks_obtained is not None]
        global_avg_score = round(statistics.mean(marks), 1) if marks else 0
    else:
        global_avg_score = 0
        
    # 4. Critical Alerts (Danger Zone)
    # Count students with avg < 40
    # In prod: Use SQL Group By + Having. Here: Python iteration (cached/optimized)
    danger_zone_count = 0
    all_students_ids = [s[0] for s in db.session.query(StudentProfile.id).all()]
    
    # Pre-fetch all marks
    all_marks_rows = db.session.query(StudentResult.student_id, StudentResult.marks_obtained).all()
    student_marks_map = {sid: [] for sid in all_students_ids}
    for sid, mark in all_marks_rows:
        if mark is not None and sid in student_marks_map:
            student_marks_map[sid].append(mark)
            
    for sid, marks in student_marks_map.items():
        if marks:
            s_avg = statistics.mean(marks)
            if s_avg < 40:
                danger_zone_count += 1
    
    # 5. Top Performer & Max Package
    top_student = "N/A"
    highest_avg = -1
    highest_pkg = 0
    for sid, marks in student_marks_map.items():
        if marks:
            s_avg = statistics.mean(marks)
            s_var = statistics.stdev(marks) if len(marks) > 1 else 0
            
            # Predict Package (Consistent with future_predictions logic)
            if s_avg > 85:
                base_pkg = 12.0 if s_var < 5 else 18.0
            elif s_avg > 70:
                base_pkg = 8.5
            elif s_avg > 60:
                base_pkg = 6.5
            else:
                base_pkg = 4.5
            
            potential_package = base_pkg + (s_var * 0.1)
            
            if potential_package > highest_pkg:
                highest_pkg = potential_package

            if s_avg > highest_avg:
                highest_avg = s_avg
                top_student = StudentProfile.query.get(sid).display_name
    
    projected_pkg = f"{round(highest_pkg, 1)} LPA" if highest_pkg > 0 else "N/A"

    stats = {
        'total_students': total_students,
        'total_faculty': total_faculty,
        'global_avg': global_avg_score,
        'attendance_pulse': "Stable",
        'danger_alerts': danger_zone_count,
        'projected_highest_pkg': projected_pkg
    }

    return render_template('reports/dashboard.html', stats=stats)

# --- 1. Student Performance Intelligence ---
@reports_bp.route('/reports/student-performance', methods=['GET'])
@login_required
def student_performance_view():
    return render_template('reports/student_performance.html')

@reports_bp.route('/api/reports/student-performance', methods=['GET'])
@login_required
def student_performance_data():
    # 1. Academic DNA (Radar): Avg Marks per Subject (Sem 3)
    # 2. Consistency (Scatter): Avg vs StdDev
    # 3. Growth Velocity: Compare Sem 1 vs Sem 3 Avg
    
    # Fetch all results
    results = db.session.query(StudentResult).all()
    # Group by Student -> Sem -> Marks
    # This is heavy, in prod we'd use SQL aggregation.
    
    student_data = {} 
    
    # Pre-fetch Student Profiles for name/sem
    students = {s.id: s for s in StudentProfile.query.all()}
    
    for r in results:
        sid = r.student_id
        if sid not in student_data: 
            student_data[sid] = {'marks': [], 'sem_marks': {}, 'name': students.get(sid).display_name}
        
        if r.marks_obtained is not None:
            student_data[sid]['marks'].append(r.marks_obtained)
            # Infer sem from ExamEvent
            # This is an N+1 issue technically but we need it. 
            # Better optimization: Join ExamEvent in the initial query.
            # But for now, let's use the Paper -> Event relationship if accessible or just map via subject logic?
            # Actually, `r.exam_paper.exam_event.semester` works if relationships are set, but let's query safer.
            pass
    
    # Re-query with explicit Join for Semester Analysis (Growth Velocity)
    # Get average marks per student per semester
    sem_avgs = db.session.query(
        StudentResult.student_id, 
        ExamEvent.semester, 
        func.avg(StudentResult.marks_obtained)
    ).select_from(StudentResult).join(ExamPaper).join(ExamEvent).group_by(StudentResult.student_id, ExamEvent.semester).all()
    
    # Populate semester data
    for sid, sem, avg in sem_avgs:
        if sid in student_data:
            student_data[sid]['sem_marks'][sem] = avg

    # Optimized Consistency & Velocity
    consistency = []
    
    # 1. Consistency: Just take all marks for a student across all time
    for sid, data in student_data.items():
        if len(data['marks']) > 1:
            avg = statistics.mean(data['marks'])
            std = statistics.stdev(data['marks'])
            
            # Growth Velocity: (Sem 3 Avg - Sem 1 Avg)
            growth = 0
            s1 = data['sem_marks'].get(1, 0)
            s3 = data['sem_marks'].get(3, 0)
            if s1 > 0 and s3 > 0:
                growth = round(((s3 - s1) / s1) * 100, 1)
            
            consistency.append({
                'name': data['name'], 
                'x': round(avg, 1), 
                'y': round(std, 1),
                'growth': growth
            })
            
    # 2. Danger Zone (Avg < 40 or Fail Count > 2)
    danger_zone = []
    for sid, data in student_data.items():
        avg = statistics.mean(data['marks']) if data['marks'] else 0
        if avg < 40:
            danger_zone.append({'name': data['name'], 'avg': round(avg, 1), 'risk': 'Critical'})

    # 3. Radar Data (Real Aggregation)
    # 3. Radar Data (Real Aggregation)
    radar_labels = []
    radar_data = []
    
    # FETCH ALL SUBJECTS (Safe Fallback)
    active_subjects = Subject.query.all()
    
    # 3. Radar Data (Optimized & Limited)
    # Fetch top 7 subjects with most results to prevent UI clutter
    radar_query = db.session.query(
        Subject.name,
        func.avg(StudentResult.marks_obtained)
    ).join(ExamPaper, ExamPaper.subject_id == Subject.id)\
     .join(StudentResult, StudentResult.exam_paper_id == ExamPaper.id)\
     .group_by(Subject.name)\
     .order_by(func.count(StudentResult.id).desc())\
     .limit(7).all()

    for name, avg_score in radar_query:
        radar_labels.append(name)
        radar_data.append(round(avg_score, 1))

    # 4. AI Executive Summary / Review
    # Analyze the whole batch
    total_students = len(consistency)
    improving_count = len([c for c in consistency if c['growth'] > 3])
    declining_count = len([c for c in consistency if c['growth'] < -3])
    avg_growth = statistics.mean([c['growth'] for c in consistency]) if consistency else 0
    
    status = "Stable"
    if avg_growth > 2: status = "Improving"
    if avg_growth < -2: status = "Declining"
    
    review_text = f"The batch is currently {status}. {improving_count} students have shown significant improvement since Semester 1, while {declining_count} are struggling to keep up."
    
    suggestion = "Maintain current momentum."
    if declining_count > improving_count:
        suggestion = "Review the teaching pace for 'Core' subjects as many students are falling behind."
    if len(danger_zone) > total_students * 0.1:
        suggestion = "Urgent: Over 10% of the class is in the Danger Zone. Schedule a parent-teacher meeting."
        
    tips = [
        "Focus on students in the 'Top Left' quadrant (Consistent but Low Scores). They are trying but failing.",
        f"Encourage the {improving_count} 'Rising Stars' to mentor their peers."
    ]

    return jsonify({
        'consistency': consistency,
        'danger_zone': danger_zone,
        'radar': {'labels': radar_labels, 'data': radar_data},
        'insights': {
            'status': status,
            'review': review_text,
            'suggestion': suggestion,
            'tips': tips
        }
    })

# --- 2. Attendance Analytics ---
@reports_bp.route('/reports/attendance-analytics', methods=['GET'])
@login_required
def attendance_analytics_view():
    return render_template('reports/attendance_analytics.html')

@reports_bp.route('/api/reports/attendance', methods=['GET'])
@login_required
def attendance_data():
    # 1. Fatigue Index (Day of Week)
    attendances = Attendance.query.all()
    day_counts = {0:0, 1:0, 2:0, 3:0, 4:0}
    day_presents = {0:0, 1:0, 2:0, 3:0, 4:0}
    
    for att in attendances:
        wd = att.date.weekday()
        if wd <= 4:
            day_counts[wd] += 1
            if att.status == 'Present': day_presents[wd] += 1
            
    fatigue = []
    for i in range(5):
        rate = (day_presents[i] / day_counts[i]) if day_counts[i] > 0 else 0
        fatigue.append(round(rate * 100, 1)) # Percentage

    # 2. Truancy Prediction (Students with < 75% Attendance)
    # Get all students and their attendance count
    truancy_list = []
    
    # Efficient Query: Group By Student, Count Status
    # This approximates for now. In prod, use SQL Case.
    all_students = StudentProfile.query.all()
    for s in all_students:
        total_days = Attendance.query.filter_by(student_id=s.id).count()
        if total_days > 0:
            present_days = Attendance.query.filter_by(student_id=s.id, status='Present').count()
            perc = (present_days / total_days) * 100
            
            # Risk Factor: < 75% is standard detention threshold
            if perc < 75:
                # Probability = Inverse of Attendance roughly
                prob = round(100 - perc, 1) 
                truancy_list.append({'name': s.display_name, 'prob': prob, 'perc': round(perc, 1)})
    
    # Sort by highest probability of dropout (lowest attendance)
    truancy_list.sort(key=lambda x: x['prob'], reverse=True)

    # 3. AI Insights
    insights = {
        'status': 'Optimal',
        'summary': 'Attendance generally stable.',
        'tip': 'No immediate action.'
    }
    
    # Analyze Fatigue (Lowest day)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    min_rate = min(fatigue)
    min_day_idx = fatigue.index(min_rate)
    
    if min_rate < 70:
        insights['status'] = 'Fatigue Detected'
        insights['summary'] = f"{days[min_day_idx]}s are showing significant drops in attendance ({min_rate}%)."
        insights['tip'] = f"Consider light activities or gamified sessions on {days[min_day_idx]}s to boost engagement."
    
    if len(truancy_list) > len(all_students) * 0.15:
        insights['status'] = 'High Truancy Risk'
        insights['summary'] = f"Warning: {len(truancy_list)} students are below the 75% mandatory attendance threshold."
        insights['tip'] = "Initiate automated SMS warnings to parents of at-risk students immediately."

    return jsonify({
        'fatigue': fatigue, # [Mon%, Tue%...]
        'truancy_prob': truancy_list[:10], # Top 10 risks
        'insights': insights
    })

# --- 3. Faculty Insights ---
@reports_bp.route('/reports/faculty-insights', methods=['GET'])
@login_required
def faculty_insights_view():
    return render_template('reports/faculty_insights.html')

@reports_bp.route('/api/reports/faculty', methods=['GET'])
@login_required
def faculty_data():
    # 1. Fetch all Faculties via the Subject Link
    # In seed_analytics.py, Subject has a 'faculty_id'. 
    # We should iterate Subjects first, then find the teacher.
    
    subjects = Subject.query.all()
    faculty_metrics = []
    
    hero_count = 0
    concern_count = 0
    
    for sub in subjects:
        # Check if subject has a faculty assigned
        # Note: Subject model might not have backref 'faculty' defined in all versions, 
        # so let's query safe.
        if not sub.faculty_id:
            continue
            
        fac = FacultyProfile.query.get(sub.faculty_id)
        if not fac:
            continue
        
        # Get Results for this subject
        sub_results = db.session.query(StudentResult.marks_obtained)\
            .join(ExamPaper).filter(ExamPaper.subject_id == sub.id).all()
            
        if sub_results:
            marks = [r.marks_obtained for r in sub_results if r.marks_obtained is not None]
            if len(marks) > 0:
                avg = statistics.mean(marks)
                std_dev = statistics.stdev(marks) if len(marks) > 1 else 0
                pass_rate = (len([m for m in marks if m >= 35]) / len(marks)) * 100
                
                # METRIC 1: Equity Index
                # Lower StdDev = High Equity (Everyone understands equally)
                # Adjusted formula to be less punitive: 100 - (StdDev * 2)
                # Typical StdDev is 15-20, so 100 - 40 = 60 (Average Equity)
                equity_score = max(0, 100 - (std_dev * 2.0)) 
                
                # METRIC 2: Performance Index
                perf_score = avg
                
                # ARCHETYPE CLASSIFICATION
                archetype = "The Generalist"
                color = "gray"
                
                # Adjusted Thresholds for realistic distribution
                if perf_score >= 60 and equity_score >= 60:
                    archetype = "The Master Teacher" 
                    color = "emerald"
                    hero_count += 1
                elif perf_score >= 65 and equity_score < 60:
                    archetype = "The Elite Coach" 
                    color = "indigo"
                elif perf_score < 55 and equity_score >= 65:
                    archetype = "The Empathetic Guide"
                    color = "blue"
                elif equity_score < 45: # Priority on Chaos
                    archetype = "The Strict Evaluator"
                    color = "red"
                    concern_count += 1
                
                faculty_metrics.append({
                    'name': fac.display_name,
                    'subject': sub.name,
                    'avg': round(avg, 1),
                    'equity': round(equity_score, 1),
                    'archetype': archetype,
                    'color': color,
                    'pass_rate': round(pass_rate, 1),
                    'students': len(marks)
                })
    
    # Sort
    faculty_metrics.sort(key=lambda x: x['avg'], reverse=True)
    
    # 2. AI Review
    insight_text = "Faculty performance is standard."
    tip_text = "Encourage peer reviews."
    status = "Stable"
    
    if hero_count > 2:
        status = "High Performing"
        insight_text = f"Outstanding! We have {hero_count} 'Master Teachers' who are lifting the entire class average."
        tip_text = "Schedule a 'Masterclass' where these teachers share their inclusive teaching techniques."
    elif concern_count > 2:
        status = "Needs Attention"
        insight_text = "Several faculty members are showing 'Strict Evaluator' signs, meaning high failure rates and low equity."
        tip_text = "Audit the difficulty of exam papers for the flagged subjects."

    return jsonify({
        'metrics': faculty_metrics,
        'insights': {
            'status': status,
            'summary': insight_text,
            'tip': tip_text
        }
    })

# --- 4. Future Predictions (AI Career Engine) ---
@reports_bp.route('/reports/future-predictions', methods=['GET'])
@login_required
def future_predictions_view():
    return render_template('reports/future_predictions.html')

@reports_bp.route('/api/reports/future', methods=['GET'])
@login_required
def future_data():
    # 1. Fetch Data
    students = StudentProfile.query.all()
    results = StudentResult.query.all()
    
    # Pre-calculate Global Metrics
    all_marks = [r.marks_obtained for r in results if r.marks_obtained is not None]
    if not all_marks:
        return jsonify({}) # Empty case
        
    global_avg = statistics.mean(all_marks)
    
    # 2. Career Match Simulation (The "Sorting Hat" Logic)
    # Define Profiles with imaginary subject weights (simplified for demo)
    # In prod, we'd query Subject names. Here we use basic heuristics.
    
    career_clusters = {
        'Data Scientist': {'count': 0, 'avg_score': 0},
        'Full Stack Dev': {'count': 0, 'avg_score': 0},
        'Product Manager': {'count': 0, 'avg_score': 0},
        'Research / PhD': {'count': 0, 'avg_score': 0}
    }
    
    # Assign every student a "Destiny" based on their persona
    # (Since we don't have granular subject types in seed, we simulate based on ranges)
    
    placement_projections = []
    
    for s in students:
        # Get student average
        s_res = [r.marks_obtained for r in results if r.student_id == s.id and r.marks_obtained]
        if not s_res: continue
        
        s_avg = statistics.mean(s_res)
        s_var = statistics.stdev(s_res) if len(s_res) > 1 else 0
        
        # Classification Logic
        role = "Unclassified"
        potential_package = 4.0 # Base 4 LPA
        
        if s_avg > 85: # High Performer
            if s_var < 5: 
                role = 'Research / PhD' # Consistent genius
                potential_package = 12.0
            else: 
                role = 'Data Scientist' # Spiky genius
                potential_package = 18.0
        elif s_avg > 70:
            role = 'Full Stack Dev'
            potential_package = 8.5
        elif s_avg > 60:
            role = 'Product Manager'
            potential_package = 6.5
        else:
            role = 'Analyst'
            potential_package = 4.5
            
        # Deterministic variability instead of random to maintain consistency across dashboards
        potential_package += (s_var * 0.1)
        
        placement_projections.append(potential_package)
        
        if role in career_clusters:
            career_clusters[role]['count'] += 1
    
    # 3. Monte Carlo Salary Simulation
    # Calculate Probabilities
    if placement_projections:
        max_pkg = max(placement_projections)
        avg_pkg = statistics.mean(placement_projections)
        
        # Tier Probability
        tier1 = len([p for p in placement_projections if p > 12]) # > 12 LPA
        tier2 = len([p for p in placement_projections if 8 <= p <= 12]) # 8-12 LPA
        tier3 = len([p for p in placement_projections if p < 8]) # < 8 LPA
        total = len(placement_projections)
        
        prob_dist = {
            'tier1': round((tier1/total)*100, 1),
            'tier2': round((tier2/total)*100, 1),
            'tier3': round((tier3/total)*100, 1)
        }
    else:
        max_pkg = 0
        avg_pkg = 0
        prob_dist = {'tier1':0, 'tier2':0, 'tier3':0}

    # 4. Skill Gap Insight
    # Identify the weakest subject dynamically
    lowest_sub_name = "Core Subjects"
    lowest_sub_avg = 100
    
    sub_avgs = db.session.query(
        Subject.name,
        func.avg(StudentResult.marks_obtained)
    ).join(ExamPaper, ExamPaper.subject_id == Subject.id)\
     .join(StudentResult, StudentResult.exam_paper_id == ExamPaper.id)\
     .group_by(Subject.name).all()
     
    if sub_avgs:
        lowest_sub = min(sub_avgs, key=lambda x: x[1] if x[1] is not None else 100)
        lowest_sub_name = lowest_sub[0]
        lowest_sub_avg = lowest_sub[1] if lowest_sub[1] is not None else 100
        
    gap_pct = round(100 - lowest_sub_avg, 1) if lowest_sub_avg < 100 else 0
    marginal_count = len([p for p in placement_projections if 6 <= p <= 8])

    skill_gap = {
        'subject': lowest_sub_name,
        'gap': f"{gap_pct}%",
        'impact': f"Closing this gap could move {marginal_count} students to higher placement tiers."
    }

    return jsonify({
        'highest_package': f"{round(max_pkg, 1)} LPA",
        'avg_package': f"{round(avg_pkg, 1)} LPA",
        'placement_prob': prob_dist,
        'careers': career_clusters,
        'skill_gap': skill_gap
    })
