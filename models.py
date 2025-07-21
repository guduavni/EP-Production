from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, ReferenceField, ListField, DictField, IntField, FileField, BooleanField
import random
import string

from werkzeug.security import generate_password_hash, check_password_hash

class User(Document):
    """
    User model for storing user details
    """
    user_id = StringField(required=True, unique=True, default=lambda: ''.join(random.choices(string.digits, k=6)))
    first_name = StringField(required=True, max_length=50)
    last_name = StringField(required=True, max_length=50)
    email = StringField(required=True, unique=True, max_length=100)
    password_hash = StringField(required=True)
    phone = StringField(max_length=20)
    role = StringField(default='candidate', choices=['admin', 'examiner', 'candidate'])
    created_at = DateTimeField(default=datetime.utcnow)
    last_login = DateTimeField()
    status = StringField(default='active', choices=['active', 'inactive', 'suspended'])
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login integration
    def get_id(self):
        return str(self.id)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_anonymous(self):
        return False
    
    meta = {
        'collection': 'users',
        'indexes': [
            {'fields': ['user_id'], 'unique': True},
            {'fields': ['email'], 'unique': True, 'sparse': False},
            'role',
            'status'
        ]
    }
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class TestScript(Document):
    """
    Test script model for storing test scenarios
    """
    script_id = StringField(required=True, unique=True, default=lambda: f"SCR{''.join(random.choices(string.digits, k=5))}")
    title = StringField(required=True, max_length=200)
    description = StringField()
    content = StringField(required=True)
    difficulty = StringField(choices=['easy', 'medium', 'hard'], default='medium')
    created_at = DateTimeField(default=datetime.utcnow)
    created_by = ReferenceField('User')
    is_active = BooleanField(default=True)
    
    meta = {
        'collection': 'test_scripts',
        'indexes': ['script_id', 'difficulty', 'is_active']
    }

class Assessment(Document):
    """
    Assessment model for test sessions
    """
    candidate = ReferenceField('User', required=True)
    examiner = ReferenceField('User')
    script = ReferenceField('TestScript')
    start_time = DateTimeField(default=datetime.utcnow)
    end_time = DateTimeField()
    status = StringField(choices=['scheduled', 'in_progress', 'completed', 'evaluated'], default='scheduled')
    
    # ICAO Assessment Criteria
    pronunciation = IntField(min_value=1, max_value=6)
    structure = IntField(min_value=1, max_value=6)
    vocabulary = IntField(min_value=1, max_value=6)
    fluency = IntField(min_value=1, max_value=6)
    comprehension = IntField(min_value=1, max_value=6)
    
    overall_score = IntField(min_value=1, max_value=6)
    notes = StringField()
    
    # Audio recordings and transcriptions
    recordings = ListField(DictField())
    
    meta = {
        'collection': 'assessments',
        'indexes': [
            'candidate',
            'examiner',
            'status',
            'start_time',
            'overall_score'
        ]
    }
    
    def calculate_overall(self):
        """Calculate overall ICAO score based on individual criteria"""
        scores = [
            self.pronunciation or 0,
            self.structure or 0,
            self.vocabulary or 0,
            self.fluency or 0,
            self.comprehension or 0
        ]
        return round(sum(scores) / len(scores)) if scores else 0

class MediaFile(Document):
    """
    Model for storing media files (images, docs, etc.)
    """
    file_id = StringField(required=True, unique=True, default=lambda: f"FILE{''.join(random.choices(string.digits + string.ascii_uppercase, k=8))}")
    filename = StringField(required=True)
    file_type = StringField(required=True)  # image, document, audio, etc.
    uploaded_by = ReferenceField('User')
    uploaded_at = DateTimeField(default=datetime.utcnow)
    description = StringField()
    file_path = StringField(required=True)
    is_active = BooleanField(default=True)
    
    meta = {
        'collection': 'media_files',
        'indexes': ['file_id', 'file_type', 'uploaded_by', 'is_active']
    }

class Report(Document):
    """
    Model for storing generated reports
    """
    report_id = StringField(required=True, unique=True, default=lambda: f"RPT{''.join(random.choices(string.digits, k=7))}")
    title = StringField(required=True)
    description = StringField()
    report_type = StringField(required=True, choices=['assessment', 'user', 'system', 'custom'])
    generated_by = ReferenceField('User')
    generated_at = DateTimeField(default=datetime.utcnow)
    parameters = DictField()  # Store report generation parameters
    file_path = StringField()  # Path to generated report file
    
    meta = {
        'collection': 'reports',
        'indexes': ['report_id', 'report_type', 'generated_by', 'generated_at']
    }

class ExamResult(Document):
    """
    Model for storing exam results and related data
    """
    exam_id = StringField(required=True, unique=True, default=lambda: f"EX{''.join(random.choices(string.digits, k=6))}")
    candidate = ReferenceField('User', required=True)
    examiner = ReferenceField('User')
    first_name = StringField(required=True, max_length=50)
    last_name = StringField(required=True, max_length=50)
    user_id = StringField(required=True, max_length=6)  # 6-digit system-generated ID
    join_date = DateTimeField(required=True, default=datetime.utcnow)
    exam_date = DateTimeField(required=True, default=datetime.utcnow)
    final_score = IntField(min_value=0, max_value=100)
    test_transcript = StringField()  # Full test transcript
    test_image = ReferenceField('MediaFile')  # Reference to image used in test
    test_script = ReferenceField('TestScript')  # Reference to the test script used
    recordings = ListField(DictField())  # List of recordings with timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'exam_results',
        'indexes': [
            'exam_id',
            'candidate',
            'examiner',
            'user_id',
            'exam_date',
            'final_score'
        ]
    }
    
    def update_timestamp(self):
        self.updated_at = datetime.utcnow()
        return self.save()
