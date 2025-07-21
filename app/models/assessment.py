"""
Assessment Models

This module defines the assessment-related models for the EP-Simulator application,
including the Assessment model and its related models.
"""
from datetime import datetime
from enum import Enum
from mongoengine import (
    EmbeddedDocument, EmbeddedDocumentField, ListField, 
    StringField, FloatField, DateTimeField, IntField, DictField, BooleanField,
    LazyReferenceField, PULL, CASCADE, Document
)

# Import base document
from .base import BaseDocument

# Import the database instance
from . import db

# Using string references to avoid circular imports
# The actual User model will be set during app initialization
from mongoengine import CASCADE

class QuestionType(Enum):
    """Types of questions in the assessment."""
    MULTIPLE_CHOICE = 'multiple_choice'
    SHORT_ANSWER = 'short_answer'
    LONG_ANSWER = 'long_answer'
    ORAL_RESPONSE = 'oral_response'
    PICTURE_DESCRIPTION = 'picture_description'
    SCENARIO = 'scenario'

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

class AssessmentStatus(Enum):
    """Status of an assessment."""
    DRAFT = 'draft'
    IN_PROGRESS = 'in_progress'
    UNDER_REVIEW = 'under_review'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'
    CANCELLED = 'cancelled'

class Assessment(BaseDocument):
    """
    Assessment model for ICAO English proficiency tests.
    """
    # Meta options
    meta = {
        'collection': 'assessments',
        'indexes': [
            # Single field indexes
            'candidate',
            'examiner',
            'status',
            'test_type',
            'scheduled_start_time',
            'scheduled_end_time',
            'is_practice',
            'is_retake',
            'assessment_date',
            'expires_at',
            'created_at',
            'updated_at',
            'completed_at',
            
            # TTL index for created_at
            {'fields': ['created_at'], 'expireAfterSeconds': 60 * 60 * 24 * 365 * 5},  # 5 years
            
            # Compound indexes
            [('candidate', 1), ('status', 1)],
            [('examiner', 1), ('status', 1)],
            [('test_type', 1), ('status', 1)],
            [('is_practice', 1), ('status', 1)]
        ],
        'ordering': ['-created_at'],
        'strict': False  # Allow dynamic fields
    }
    
    # Status constants
    STATUS_CHOICES = [status.value for status in AssessmentStatus]
    
    # Test type constants
    TEST_TYPE_OPI = 'opi'  # Oral Proficiency Interview
    TEST_TYPE_EAP = 'eap'  # English for Aviation Purposes
    TEST_TYPE_LPE = 'lpe'  # Language Proficiency Exam
    TEST_TYPE_CHOICES = (TEST_TYPE_OPI, TEST_TYPE_EAP, TEST_TYPE_LPE)
    
    # Relationships - using string references to avoid circular imports
    candidate = LazyReferenceField('User', required=True, reverse_delete_rule=CASCADE, passthrough=True)
    examiner = LazyReferenceField('User', reverse_delete_rule=CASCADE, required=False, passthrough=True)
    previous_assessment = LazyReferenceField('self', reverse_delete_rule=CASCADE, required=False, passthrough=True)
    
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
    questions = ListField(EmbeddedDocumentField(Question))
    recordings = ListField(EmbeddedDocumentField(AudioRecording))
    
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
            
            # Update candidate's assessment history
            if self.candidate:
                self.candidate.update(add_to_set__completed_assessments=self)
                self.candidate.save()
            
            # Notify examiner if applicable
            if self.examiner:
                notification = Notification(
                    user=self.examiner,
                    title=f"Assessment Completed: {self.title}",
                    message=f"{self.candidate.get_full_name() or 'A candidate'} has completed the assessment.",
                    notification_type='assessment_completed',
                    related_document_id=str(self.id)
                )
                notification.save()
            
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
