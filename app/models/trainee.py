from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, ReferenceField, ListField, EmbeddedDocument, EmbeddedDocumentField, EmailField, BooleanField
from .user import User

class TraineeProgress(EmbeddedDocument):
    """Tracks progress of a trainee in different areas"""
    area = StringField(required=True)
    level = StringField(required=True)
    notes = StringField()
    updated_at = DateTimeField(default=datetime.utcnow)

class Trainee(Document):
    """Trainee model for storing trainee information"""
    meta = {
        'collection': 'trainees',
        'indexes': [
            'user',
            'status',
            'training_program'
        ]
    }
    
    # Basic Information
    user = ReferenceField(User, required=True, unique=True)
    id_number = StringField(required=True, unique=True)
    date_of_birth = DateTimeField(required=True)
    phone = StringField(required=True)
    address = StringField(required=True)
    city = StringField(required=True)
    
    # Training Information
    training_program = StringField(required=True)
    start_date = DateTimeField(required=True)
    end_date = DateTimeField()
    status = StringField(required=True, choices=(
        'active', 'completed', 'dropped', 'on_hold'), default='active')
    
    # Emergency Contact
    emergency_contact_name = StringField(required=True)
    emergency_contact_phone = StringField(required=True)
    emergency_contact_relation = StringField(required=True)
    
    # Progress Tracking
    progress = ListField(EmbeddedDocumentField(TraineeProgress))
    
    # Documents
    documents = ListField(StringField())  # Store document file paths
    
    # System Fields
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def clean(self):
        """Ensure end_date is after start_date if provided"""
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date must be after start date')
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.name} ({self.id_number})"
