"""
Assessment Models

This module defines the assessment-related models for the EP-Simulator application,
including the Assessment model and its related models.
"""
from datetime import datetime
from enum import Enum
from mongoengine import (
    Document, EmbeddedDocument, 
    StringField, DateTimeField, 
    ListField, EmbeddedDocumentField,
    ReferenceField, LazyReferenceField,
    BooleanField, IntField, FloatField,
    DictField, URLField, FileField
)
# Delete rule constants
NULLIFY = 1
CASCADE = 2
DENY = 3
DO_NOTHING = 4
PULL = 5
from mongoengine import register_connection, get_connection

# Import base document first
from .base import BaseDocument

# Import the database instance from extensions
from app.extensions import db

# Import enums first to avoid circular imports
class QuestionType(Enum):
    """Types of questions in the assessment."""
    MULTIPLE_CHOICE = 'multiple_choice'
    SHORT_ANSWER = 'short_answer'
    LONG_ANSWER = 'long_answer'
    ORAL_RESPONSE = 'oral_response'
    PICTURE_DESCRIPTION = 'picture_description'
    SCENARIO = 'scenario'

class AssessmentStatus(Enum):
    """Status of an assessment."""
    DRAFT = 'draft'
    IN_PROGRESS = 'in_progress'
    UNDER_REVIEW = 'under_review'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'
    CANCELLED = 'cancelled'

class Question(EmbeddedDocument):
    """
    Embedded document representing a question in an assessment.
    """
    # Question details
    question_type = StringField(choices=[t.value for t in QuestionType], required=True)
    text = StringField(required=True)
    description = StringField()
    
    # Question options (for multiple choice)
    options = ListField(StringField())
    correct_answer = StringField()
    
    # Response
    answer = StringField()
    score = FloatField(min_value=0, max_value=6, default=0)
    feedback = StringField()
    
    # Audio recording (for oral responses)
    audio_recording = StringField()
    audio_duration = FloatField()
    
    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        """Convert the question to a dictionary."""
        return {
            'id': str(self.id),
            'question_type': self.question_type,
            'text': self.text,
            'description': self.description,
            'options': self.options,
            'answer': self.answer,
            'score': self.score,
            'feedback': self.feedback,
            'audio_recording': self.audio_recording,
            'audio_duration': self.audio_duration,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AudioRecording(EmbeddedDocument):
    """
    Embedded document representing an audio recording in an assessment.
    """
    # File information
    file_path = StringField(required=True)
    file_name = StringField(required=True)
    file_size = IntField()  # in bytes
    file_type = StringField()
    
    # Audio metadata
    duration = FloatField(required=True)  # in seconds
    sample_rate = IntField()  # in Hz
    channels = IntField(default=1)
    
    # Transcription and analysis
    transcript = StringField()
    confidence = FloatField(min_value=0, max_value=1)  # confidence score of the transcript
    language = StringField(default='en')
    
    # Processing status
    is_processed = BooleanField(default=False)
    processing_error = StringField()
    
    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    processed_at = DateTimeField()
    
    def to_dict(self):
        """Convert the audio recording to a dictionary."""
        return {
            'id': str(self.id),
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'transcript': self.transcript,
            'confidence': self.confidence,
            'language': self.language,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class Assessment(BaseDocument):
    """
    Assessment model for ICAO English proficiency tests.
    """
    # Meta options
    meta = {
        'collection': 'assessments',
        'indexes': [
            # Explicitly named single field indexes
            {'fields': ['created_by'], 'name': 'created_by_idx'},
            {'fields': ['assigned_to'], 'name': 'assigned_to_idx', 'sparse': True},
            {'fields': ['status'], 'name': 'status_idx'},
            {'fields': ['test_type'], 'name': 'test_type_idx'},
            {'fields': ['created_at'], 'name': 'created_at_idx'},
            {'fields': ['expires_at'], 'name': 'expires_at_ttl', 'expireAfterSeconds': 0},
            
            # Compound indexes with explicit names
            {
                'fields': ['created_by', 'status'],
                'name': 'created_by_status_idx'
            },
            {
                'fields': ['assigned_to', 'status'],
                'name': 'assigned_to_status_idx',
                'sparse': True
            },
            {
                'fields': ['test_type', 'status'],
                'name': 'test_type_status_idx'
            },
            # Text index for search
            {
                'fields': ['$title', '$description', '$feedback', '$examiner_notes'],
                'default_language': 'english',
                'weights': {
                    'title': 10,
                    'description': 5,
                    'feedback': 5,
                    'examiner_notes': 3
                },
                'name': 'assessment_search_text'
            }
        ],
        'ordering': ['-created_at'],
        'strict': False,  # Allow dynamic fields
        'auto_create_index': False  # Prevent automatic index creation
    }
    
    # Assessment status choices
    STATUS_CHOICES = [status.value for status in AssessmentStatus]
    
    # Test type choices
    TEST_TYPE_OPI = 'opi'
    TEST_TYPE_EAP = 'eap'
    TEST_TYPE_LPE = 'lpe'
    TEST_TYPE_CHOICES = (TEST_TYPE_OPI, TEST_TYPE_EAP, TEST_TYPE_LPE)
    
    # Relationships - using string references to avoid circular imports
    created_by = LazyReferenceField('User', required=True, passthrough=False, dbref=True, allow_none=False)
    assigned_to = LazyReferenceField('User', required=False, passthrough=False, dbref=True, allow_none=True)
    assigned_by = LazyReferenceField('User', required=False, passthrough=False, dbref=True, allow_none=True)
    
    # Disable automatic registration of delete rules
    def clean(self):
        """Ensure required fields are set before validation."""
        # Set default values if not provided
        if not hasattr(self, 'status'):
            self.status = AssessmentStatus.DRAFT.value
        if not hasattr(self, 'test_type'):
            self.test_type = self.TEST_TYPE_OPI
        if not hasattr(self, 'progress'):
            self.progress = 0
            
        # Set timestamps
        now = datetime.utcnow()
        if not hasattr(self, 'created_at'):
            self.created_at = now
        self.updated_at = now
            
    def save(self, *args, **kwargs):
        """Override save to ensure clean is called and handle indexes."""
        self.clean()
        return super().save(*args, **kwargs)
    
    def __init__(self, *args, **kwargs):
        super(Assessment, self).__init__(*args, **kwargs)
        # Manually set up delete rules after all models are loaded
        if not hasattr(self, '_delete_rules_setup'):
            self._delete_rules_setup = True
            from mongoengine import signals
            signals.post_init.connect(self._setup_delete_rules, sender=self.__class__)
    
    def _setup_delete_rules(self, *args, **kwargs):
        """Manually set up delete rules after all models are loaded."""
        try:
            from mongoengine import get_document
            User = get_document('User')
            if hasattr(self, 'created_by') and self.created_by:
                self.created_by._meta['delete_rules'] = self.created_by._meta.get('delete_rules', {})
                self.created_by._meta['delete_rules']['created_assessments'] = (self.__class__, 'NULLIFY')
            if hasattr(self, 'assigned_to') and self.assigned_to:
                self.assigned_to._meta['delete_rules'] = self.assigned_to._meta.get('delete_rules', {})
                self.assigned_to._meta['delete_rules']['assigned_assessments'] = (self.__class__, 'PULL')
            if hasattr(self, 'assigned_by') and self.assigned_by:
                self.assigned_by._meta['delete_rules'] = self.assigned_by._meta.get('delete_rules', {})
                self.assigned_by._meta['delete_rules']['assigned_by_assessments'] = (self.__class__, 'DENY')
        except Exception as e:
            import logging
            logging.error(f"Error setting up delete rules: {e}")
    
    # Assessment details
    title = StringField(required=True, max_length=200)
    description = StringField()
    test_type = StringField(choices=TEST_TYPE_CHOICES, default=TEST_TYPE_OPI)
    status = StringField(choices=STATUS_CHOICES, default=AssessmentStatus.DRAFT.value)
    progress = IntField(min_value=0, max_value=100, default=0)
    
    # Scheduling
    scheduled_start_time = DateTimeField()
    scheduled_end_time = DateTimeField()
    started_at = DateTimeField()
    completed_at = DateTimeField()
    time_limit = IntField()  # in minutes
    
    # Assessment sections
    introduction = StringField()
    picture_description = StringField()
    scenario = StringField()
    
    # Questions and recordings
    questions = ListField(EmbeddedDocumentField('Question'))
    recordings = ListField(EmbeddedDocumentField('AudioRecording'))
    
    # ICAO scores
    pronunciation_score = FloatField(min_value=0, max_value=6, default=0)
    structure_score = FloatField(min_value=0, max_value=6, default=0)
    vocabulary_score = FloatField(min_value=0, max_value=6, default=0)
    fluency_score = FloatField(min_value=0, max_value=6, default=0)
    comprehension_score = FloatField(min_value=0, max_value=6, default=0)
    interaction_score = FloatField(min_value=0, max_value=6, default=0)
    overall_score = FloatField(min_value=0, max_value=6, default=0)
    
    # ICAO level
    icao_level = StringField(choices=[
        ('1', 'Pre-elementary'),
        ('2', 'Elementary'),
        ('3', 'Pre-operational'),
        ('4', 'Operational'),
        ('5', 'Extended'),
        ('6', 'Expert')
    ])
    
    # Examiner's comments and recommendations
    strengths = StringField()
    areas_for_improvement = StringField()
    recommendations = StringField()
    examiner_notes = StringField()
    feedback = StringField()
    
    # Flags
    is_practice = BooleanField(default=False)
    is_retake = BooleanField(default=False)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    assessment_date = DateTimeField(default=datetime.utcnow)
    expires_at = DateTimeField()
    
    # Methods
    def calculate_scores(self):
        """Calculate overall scores based on individual question scores."""
        if not self.questions:
            return
            
        total_score = 0
        count = 0
        
        for question in self.questions:
            if question.score is not None:
                total_score += question.score
                count += 1
        
        if count > 0:
            self.overall_score = round(total_score / count, 1)
            self.icao_level = self.determine_icao_level(self.overall_score)
    
    @staticmethod
    def determine_icao_level(score):
        """Determine ICAO level based on the score."""
        if score >= 5.5:
            return '6'  # Expert
        elif score >= 4.5:
            return '5'  # Extended
        elif score >= 3.5:
            return '4'  # Operational
        elif score >= 2.5:
            return '3'  # Pre-operational
        elif score >= 1.5:
            return '2'  # Elementary
        else:
            return '1'  # Pre-elementary
    
    def add_question(self, question_type, text, **kwargs):
        """Add a new question to the assessment."""
        question = Question(
            question_type=question_type,
            text=text,
            **kwargs
        )
        self.questions.append(question)
        return question
    
    def add_recording(self, file_path, file_name, duration, **kwargs):
        """Add a new audio recording to the assessment."""
        recording = AudioRecording(
            file_path=file_path,
            file_name=file_name,
            duration=duration,
            **kwargs
        )
        self.recordings.append(recording)
        return recording
    
    def start_assessment(self):
        """Mark the assessment as started."""
        if self.status == AssessmentStatus.DRAFT.value:
            self.status = AssessmentStatus.IN_PROGRESS.value
            self.started_at = datetime.utcnow()
            if self.scheduled_start_time is None:
                self.scheduled_start_time = self.started_at
            
            # Set expiration time if time limit is set
            if self.time_limit:
                self.expires_at = datetime.utcnow() + timedelta(minutes=self.time_limit)
    
    def complete_assessment(self):
        """Mark the assessment as completed."""
        if self.status in [AssessmentStatus.IN_PROGRESS.value, AssessmentStatus.UNDER_REVIEW.value]:
            self.status = AssessmentStatus.COMPLETED.value
            self.completed_at = datetime.utcnow()
            self.progress = 100
            
            # Calculate overall score if not already calculated
            if not self.overall_score:
                self.calculate_overall_score()
            
            # Update user's assessment history if created_by is set
            if self.created_by:
                try:
                    from .user import User
                    user = User.objects.get(id=self.created_by.id)
                    user.update(add_to_set__completed_assessments=self)
                    user.save()
                except Exception as e:
                    import logging
                    logging.error(f"Error updating user's assessment history: {e}")
            
            # Notify assigned_to user if applicable
            if self.assigned_to and self.assigned_to != self.created_by:
                try:
                    from .notification import Notification
                    user_name = self.created_by.get_full_name() if hasattr(self.created_by, 'get_full_name') else 'A user'
                    notification = Notification(
                        user=self.assigned_to,
                        title=f"Assessment Completed: {self.title}",
                        message=f"{user_name} has completed the assessment.",
                        notification_type='assessment_completed',
                        related_document_id=str(self.id)
                    )
                    notification.save()
                except Exception as e:
                    import logging
                    logging.error(f"Error sending notification: {e}")
            
            self.save()
            return True
        return False
    
    def submit_for_review(self):
        """Submit the assessment for examiner review."""
        if self.status == AssessmentStatus.IN_PROGRESS.value:
            self.status = AssessmentStatus.UNDER_REVIEW.value
    
    def archive(self):
        """Archive the assessment."""
        if self.status != AssessmentStatus.ARCHIVED.value:
            self.status = AssessmentStatus.ARCHIVED.value
    
    def to_dict(self, include_questions=True, include_recordings=False):
        """Convert the assessment to a dictionary."""
        data = super().to_dict()
        
        # Add related objects
        if include_questions and 'questions' in data:
            data['questions'] = [q.to_dict() for q in self.questions]
            
        if include_recordings and 'recordings' in data:
            data['recordings'] = [r.to_dict() for r in self.recordings]
        
        # Add computed fields
        data['duration'] = self.duration
        data['is_expired'] = self.is_expired
        data['is_scored'] = self.is_scored
        
        return data
    
    @property
    def duration(self):
        """Calculate the duration of the assessment in minutes."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 60
        return None
    
    @property
    def is_expired(self):
        """Check if the assessment has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @property
    def is_scored(self):
        """Check if the assessment has been fully scored."""
        required_scores = [
            self.pronunciation_score,
            self.structure_score,
            self.vocabulary_score,
            self.fluency_score,
            self.comprehension_score,
            self.interaction_score,
            self.overall_score
        ]
        return all(score is not None for score in required_scores)
    
    def calculate_overall_score(self):
        """Calculate the overall score based on individual ICAO scores."""
        scores = [
            self.pronunciation_score,
            self.structure_score,
            self.vocabulary_score,
            self.fluency_score,
            self.comprehension_score,
            self.interaction_score
        ]
        
        if all(score is not None for score in scores):
            self.overall_score = round(sum(scores) / len(scores), 1)
            self.icao_level = self.determine_icao_level(self.overall_score)
            self.save()
            return self.overall_score
        return None
    
    def determine_icao_level(self, score):
        """Determine ICAO level based on the score."""
        if score >= 5.5:
            return '6'  # Expert
        elif score >= 4.5:
            return '5'  # Extended
        elif score >= 3.5:
            return '4'  # Operational
        elif score >= 2.5:
            return '3'  # Pre-operational
        elif score >= 1.5:
            return '2'  # Elementary
        else:
            return '1'  # Pre-elementary
    
    def add_question(self, question_type, text, **kwargs):
        """Add a new question to the assessment."""
        question = Question(
            question_type=question_type,
            text=text,
            **kwargs
        )
        self.questions.append(question)
        return question
    
    def add_recording(self, file_path, file_name, duration, **kwargs):
        """Add a new audio recording to the assessment."""
        recording = AudioRecording(
            file_path=file_path,
            file_name=file_name,
            duration=duration,
            **kwargs
        )
        self.recordings.append(recording)
        return recording

    def start_assessment(self):
        """Mark the assessment as started."""
        if self.status == AssessmentStatus.DRAFT.value:
            self.status = AssessmentStatus.IN_PROGRESS.value
            self.started_at = datetime.utcnow()
            if self.scheduled_start_time is None:
                self.scheduled_start_time = self.started_at
            
            # Set expiration time if time limit is set
            if self.time_limit:
                self.expires_at = datetime.utcnow() + timedelta(minutes=self.time_limit)
            
            self.save()
            return True
        return False
        
    def __str__(self):
        """String representation of the assessment."""
        return f"{self.title} - {self.status}"

# Register the models after they're defined
from . import registry
registry.register('Question', Question)
registry.register('AudioRecording', AudioRecording)
registry.register('Assessment', Assessment)

# Export the models
__all__ = ['Assessment', 'Question', 'AudioRecording']
