"""
User Model

This module defines the User model for the application, handling authentication,
authorization, and user management.
"""
import re
from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired
from mongoengine import (
    StringField, EmailField, DateTimeField, BooleanField, 
    ListField, ReferenceField, LazyReferenceField, IntField, DictField, 
    PULL, CASCADE
)

# Import base document
from .base import BaseDocument

# Import the database instance
from . import db

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

class User(BaseDocument, UserMixin):
    """
    User model for authentication and authorization.
    
    This model handles user accounts, authentication, and role-based access control.
    """
    
    # Role constants
    ROLE_ADMIN = 'admin'
    ROLE_EXAMINER = 'examiner'
    ROLE_CANDIDATE = 'candidate'
    ROLE_CHOICES = (ROLE_ADMIN, ROLE_EXAMINER, ROLE_CANDIDATE)
    
    # Status constants
    STATUS_ACTIVE = 'active'
    STATUS_PENDING = 'pending'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = (STATUS_ACTIVE, STATUS_PENDING, STATUS_SUSPENDED)
    
    # Meta options
    meta = {
        'collection': 'users',
        'indexes': [
            # Single field indexes
            'email',
            'role',
            'is_active',
            'email_verified',
            'last_login',
            'created_at',
            'updated_at',
            
            # TTL index for temporary data
            {'fields': ['created_at'], 'expireAfterSeconds': 60 * 60 * 24 * 30 * 6},  # 6 months
            
            # Compound indexes
            [('email', 1), ('is_active', 1)],
            [('role', 1), ('is_active', 1)],
            [('status', 1), ('is_active', 1)],
            [('last_login', -1)],
            [('created_at', -1)],
            [('updated_at', -1)],
            
            # Text index for search
            {
                'fields': ['$email', '$first_name', '$last_name', '$name'],
                'default_language': 'english',
                'weights': {'email': 10, 'name': 5, 'first_name': 5, 'last_name': 5}
            }
        ],
        'ordering': ['-created_at'],
        'strict': False  # Allow dynamic fields
    }
    
    # Authentication fields
    email = EmailField(required=True, unique=True, max_length=255)
    password_hash = StringField(required=True, max_length=255)
    is_active = BooleanField(default=True)
    email_verified = BooleanField(default=False)
    
    # Profile information
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=50)
    name = StringField(required=True, max_length=100)  # Full name
    title = StringField(max_length=100)
    organization = StringField(max_length=100)
    phone = StringField(max_length=20)
    avatar_url = StringField()
    bio = StringField(max_length=500)
    timezone = StringField(default='UTC')
    language = StringField(default='en')
    
    # Role and status
    role = StringField(choices=ROLE_CHOICES, default=ROLE_CANDIDATE)
    status = StringField(choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    roles = ListField(ReferenceField('Role', reverse_delete_rule=PULL, required=False))
    permissions = ListField(StringField())
    
    # Authentication tracking
    last_login = DateTimeField()
    last_activity = DateTimeField()
    login_attempts = IntField(default=0)
    locked_until = DateTimeField()
    
    # Email verification
    email_verification_token = StringField()
    email_verification_sent_at = DateTimeField()
    
    # Password reset
    reset_password_token = StringField()
    reset_password_sent_at = DateTimeField()
    
    # Security
    current_sign_in_ip = StringField()
    last_sign_in_ip = StringField()
    sign_in_count = IntField(default=0)
    failed_login_attempts = IntField(default=0)
    account_locked_until = DateTimeField()
    
    # Preferences
    preferences = DictField(default={
        'theme': 'light',
        'notifications': True,
        'email_notifications': True,
        'language': 'en'
    })
    
    # Profile
    profile_picture = StringField()
    
    # Relationships - using string references to avoid circular imports
    assessments = ListField(LazyReferenceField('Assessment', reverse_delete_rule=PULL, required=False, passthrough=True))
    created_assessments = ListField(LazyReferenceField('Assessment', reverse_delete_rule=PULL, required=False, passthrough=True))
    
    # Audit fields
    created_by = StringField()
    updated_by = StringField()
    deleted_by = StringField()
    
    # Set the collection name explicitly to avoid issues with model registration
    meta = {
        'collection': 'users',
        'indexes': [
            'email',
            'is_active',
            'email_verified',
            'role',
            'status',
            'created_at',
            {'fields': ['email'], 'unique': True},
            {'fields': ['email_verification_token'], 'sparse': True},
            {'fields': ['reset_password_token'], 'sparse': True},
            {'fields': ['created_at'], 'expireAfterSeconds': 60 * 60 * 24 * 365}  # 1 year TTL
        ]
    }
    
    # Timestamps
    password_changed_at = DateTimeField()
    
    # Methods
    def __init__(self, *args, **kwargs):
        """Initialize the user with default values."""
        super(User, self).__init__(*args, **kwargs)
        if not self.preferences:
            self.preferences = {
                'theme': 'light',
                'notifications': True,
                'language': 'en'
            }
    
    def set_password(self, password):
        """Set the user's password."""
        if not password or len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def generate_auth_token(self, expiration=3600):
        """Generate an authentication token for the user."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': str(self.id)})
    
    @classmethod
    def verify_auth_token(cls, token):
        """Verify an authentication token and return the user if valid."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=3600)  # 1 hour expiration
        except (BadSignature, SignatureExpired):
            return None
        return cls.objects(id=data['id']).first()
    
    def generate_reset_token(self, expiration=3600):
        """Generate a password reset token."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        self.reset_password_token = s.dumps({'reset': str(self.id)})
        self.reset_password_sent_at = datetime.utcnow()
        self.save()
        return self.reset_password_token
    
    @classmethod
    def verify_reset_token(cls, token):
        """Verify a password reset token and return the user if valid."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=3600)  # 1 hour expiration
        except (BadSignature, SignatureExpired):
            return None
            
        user = cls.objects(id=data['reset']).first()
        if user is None or user.reset_password_token != token:
            return None
            
        # Token is valid for 1 hour by default
        if (datetime.utcnow() - user.reset_password_sent_at).total_seconds() > 3600:
            return None
            
        return user
    
    def generate_email_verification_token(self, expiration=86400):
        """Generate an email verification token."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        self.email_verification_token = s.dumps({'verify': str(self.id)})
        self.email_verification_sent_at = datetime.utcnow()
        self.save()
        return self.email_verification_token
    
    def verify_email(self, token):
        """Verify an email verification token."""
        if self.email_verified:
            return True
            
        if not self.email_verification_token or self.email_verification_token != token:
            return False
            
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=86400)  # 24 hours expiration
        except (BadSignature, SignatureExpired):
            return False
            
        if data['verify'] != str(self.id):
            return False
            
        self.email_verified = True
        self.email_verification_token = None
        self.save()
        return True
    
    def record_login(self, ip_address):
        """Record a successful login."""
        self.last_sign_in_ip = self.current_sign_in_ip
        self.current_sign_in_ip = ip_address
        self.last_login = datetime.utcnow()
        self.sign_in_count += 1
        self.login_attempts = 0
        self.locked_until = None
        self.save()
    
    def record_failed_login(self):
        """Record a failed login attempt."""
        max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
        lockout_time = current_app.config.get('ACCOUNT_LOCKOUT_MINUTES', 15)
        
        self.login_attempts += 1
        
        if self.login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_time)
        
        self.save()
    
    def is_locked(self):
        """Check if the account is locked due to too many failed login attempts."""
        if not self.locked_until:
            return False
            
        if self.locked_until > datetime.utcnow():
            return True
            
        # Clear the lock if it's expired
        self.login_attempts = 0
        self.locked_until = None
        self.save()
        return False
    
    def has_role(self, role):
        """Check if the user has the specified role."""
        return self.role == role
    
    def has_any_role(self, *roles):
        """Check if the user has any of the specified roles."""
        return self.role in roles
    
    @property
    def is_admin(self):
        """Check if the user is an admin."""
        return self.role == self.ROLE_ADMIN
    
    @property
    def is_examiner(self):
        """Check if the user is an examiner."""
        return self.role == self.ROLE_EXAMINER
    
    @property
    def is_candidate(self):
        """Check if the user is a candidate."""
        return self.role == self.ROLE_CANDIDATE
    
    @property
    def is_authenticated(self):
        """Check if the user is authenticated."""
        return True
    
    @property
    def is_anonymous(self):
        """Check if the user is anonymous."""
        return False
    
    def get_id(self):
        """Get the user's ID as a string."""
        return str(self.id)
    
    def to_dict(self, include_sensitive=False):
        """Convert the user to a dictionary."""
        data = super().to_dict()
        
        # Remove sensitive information
        if not include_sensitive:
            data.pop('password_hash', None)
            data.pop('reset_password_token', None)
            data.pop('email_verification_token', None)
            data.pop('current_sign_in_ip', None)
            data.pop('last_sign_in_ip', None)
        
        # Add computed properties
        data['is_admin'] = self.is_admin
        data['is_examiner'] = self.is_examiner
        data['is_candidate'] = self.is_candidate
        
        return data
    
    @classmethod
    def create_user(cls, email, password, name, role=ROLE_CANDIDATE, **kwargs):
        """Create a new user with the given information."""
        if not email or not EMAIL_REGEX.match(email):
            raise ValueError('Invalid email address')
            
        if cls.objects(email=email).first():
            raise ValueError('Email already in use')
            
        user = cls(email=email, name=name, role=role, **kwargs)
        user.set_password(password)
        user.save()
        return user
    
    @classmethod
    def get_by_email(cls, email):
        """Get a user by email address."""
        return cls.objects(email=email).first()
    
    @classmethod
    def get_admins(cls):
        """Get all admin users."""
        return cls.objects(role=cls.ROLE_ADMIN, is_active=True)
    
    @classmethod
    def get_examiners(cls):
        """Get all examiner users."""
        return cls.objects(role=cls.ROLE_EXAMINER, is_active=True)
    
    @classmethod
    def get_candidates(cls):
        """Get all candidate users."""
        return cls.objects(role=cls.ROLE_CANDIDATE, is_active=True)
    
    def __str__(self):
        """String representation of the user."""
        return f"{self.name} <{self.email}>"
    
    def is_candidate(self):
        return self.role == 'candidate'
    
    def __str__(self):
        return f"{self.name} <{self.email}>"

# Export the User model
__all__ = ['User']
