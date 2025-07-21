import os
import sys
import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from mongoengine import connect
from models import User, TestScript, ExamResult, MediaFile, Assessment, Report
from simple_app import create_app

def generate_user_id():
    """Generate a random 6-digit user ID"""
    return ''.join(random.choices(string.digits, k=6))

def generate_exam_id():
    """Generate a random 6-digit exam ID"""
    return ''.join(random.choices(string.digits, k=6))

def create_test_users():
    """Create test users with different roles"""
    users = [
        {
            'email': 'admin@example.com',
            'password': 'admin123',
            'first_name': 'מנהל',
            'last_name': 'מערכת',
            'role': 'admin',
            'status': 'active'
        },
        {
            'email': 'examiner@example.com',
            'password': 'examiner123',
            'first_name': 'בוחן',
            'last_name': 'מערכת',
            'role': 'examiner',
            'status': 'active'
        },
        {
            'email': 'candidate@example.com',
            'password': 'candidate123',
            'first_name': 'נבחן',
            'last_name': 'מבחן',
            'role': 'candidate',
            'status': 'active'
        }
    ]
    
    created_users = []
    for user_data in users:
        if not User.objects(email=user_data['email']).first():
            user = User(
                user_id=generate_user_id(),
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password=generate_password_hash(user_data['password']),
                role=user_data['role'],
                status=user_data['status']
            )
            user.save()
            created_users.append(user)
            print(f"Created user: {user.email}")
    
    return created_users

def create_test_scripts():
    """Create test scripts with different difficulty levels"""
    scripts = [
        {
            'title': 'תסריט מבחן - רמה קלה',
            'description': 'תרגילי דיבור בסיסיים',
            'content': 'בצע את התרגילים הבאים: 1. הצג את עצמך 2. תאר את ביתך 3. מה התחביבים שלך?',
            'difficulty': 'easy',
            'is_active': True
        },
        {
            'title': 'תסריט מבחן - רמה בינונית',
            'description': 'תרגילי דיבור מורכבים',
            'content': 'בצע את התרגילים הבאים: 1. תאר חוויה מלחיצה 2. מה דעתך על טכנולוגיה בחיינו?',
            'difficulty': 'medium',
            'is_active': True
        },
        {
            'title': 'תסריט מבחן - רמה מתקדמת',
            'description': 'תרגילי דיבור מורכבים מאוד',
            'content': 'בצע את התרגילים הבאים: 1. נאום של 3 דקות על נושא לבחירתך 2. דיון בנושא אקטואליה',
            'difficulty': 'hard',
            'is_active': True
        }
    ]
    
    created_scripts = []
    for script_data in scripts:
        if not TestScript.objects(title=script_data['title']).first():
            script = TestScript(
                script_id=generate_user_id(),  # Reusing the same function for script ID
                title=script_data['title'],
                description=script_data['description'],
                content=script_data['content'],
                difficulty=script_data['difficulty'],
                is_active=script_data['is_active']
            )
            script.save()
            created_scripts.append(script)
            print(f"Created test script: {script.title}")
    
    return created_scripts

def create_test_exam_results(users, scripts):
    """Create test exam results"""
    candidates = [u for u in users if u.role == 'candidate']
    examiners = [u for u in users if u.role == 'examiner']
    
    if not candidates or not examiners or not scripts:
        print("Need at least one candidate, examiner, and script to create exam results")
        return []
    
    exam_results = []
    for i in range(5):
        candidate = random.choice(candidates)
        examiner = random.choice(examiners)
        script = random.choice(scripts)
        
        exam = ExamResult(
            exam_id=generate_exam_id(),
            candidate=candidate,
            examiner=examiner,
            first_name=candidate.first_name,
            last_name=candidate.last_name,
            user_id=candidate.user_id,
            exam_date=datetime.now() - timedelta(days=random.randint(1, 30)),
            final_score=random.randint(50, 100),
            test_transcript=f"תמליל מבחן לדוגמה עבור {candidate.first_name} {candidate.last_name}",
            test_script=script
        )
        exam.save()
        exam_results.append(exam)
        print(f"Created exam result for {candidate.email} with score {exam.final_score}")
    
    return exam_results

def create_admin_user(email, password, first_name, last_name):
    """Create an admin user in the database"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        if User.objects(email=email).first():
            print(f"Admin user with email {email} already exists.")
            return False
        
        # Create admin user
        admin = User(
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role='admin',
            is_active=True,
            email_confirmed=True
        )
        
        admin.save()
        print(f"Admin user {email} created successfully!")
        return True

def initialize_database():
    """Initialize the database with test data"""
    print("Initializing database...")
    
    # Create test data
    print("\nCreating test users...")
    users = create_test_users()
    
    print("\nCreating test scripts...")
    scripts = create_test_scripts()
    
    print("\nCreating test exam results...")
    exams = create_test_exam_results(users, scripts)
    
    print("\nDatabase initialization complete!")
    print(f"Created {len(users)} users, {len(scripts)} scripts, and {len(exams)} exam results.")

if __name__ == '__main__':
    # Support both interactive mode and command-line mode
    if len(sys.argv) == 1:
        # Interactive mode - create all test data
        initialize_database()
    elif len(sys.argv) == 5:
        # Command-line mode - create admin user only
        email = sys.argv[1]
        password = sys.argv[2]
        first_name = sys.argv[3]
        last_name = sys.argv[4]
        
        # Create app context
        app = create_app()
        with app.app_context():
            create_admin_user(email, password, first_name, last_name)
    else:
        print("Usage:")
        print("  Interactive mode (creates test data): python init_db.py")
        print("  Command-line mode (creates admin user): python init_db.py <email> <password> <first_name> <last_name>")
        sys.exit(1)
