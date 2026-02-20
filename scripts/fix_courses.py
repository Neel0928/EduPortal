import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Course

app = create_app()

with app.app_context():
    existing = [c.code for c in Course.query.all()]
    print('Existing courses:', existing)
    
    needed = [
        {'name': 'Bachelor of Technology', 'code': 'B.Tech', 'dept': 'Engineering', 'dur': 4, 'sem': 8},
        {'name': 'Bachelor of Computer Applications', 'code': 'BCA', 'dept': 'Computer Science', 'dur': 3, 'sem': 6},
        {'name': 'Master of Computer Applications', 'code': 'MCA', 'dept': 'Computer Science', 'dur': 2, 'sem': 4}
    ]
    
    for n in needed:
        if n['code'] not in existing:
            c = Course(
                name=n['name'], 
                code=n['code'], 
                department=n['dept'], 
                duration_years=n['dur'], 
                total_semesters=n['sem']
            )
            db.session.add(c)
            print(f'Added {n["code"]}')
    
    db.session.commit()
    print('Done.')
