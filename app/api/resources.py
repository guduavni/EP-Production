"""
API Resources

This module contains the API resource classes for the EP-Simulator application.
"""
from flask import request, jsonify, current_app, g
from flask_restful import Resource, reqparse, abort
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

# Local imports
from ..models import User, Assessment, Question, AudioRecording
from ..utils.decorators import admin_required, examiner_required
from ..utils.audio_processing import process_audio_file

# Request parsers
assessment_parser = reqparse.RequestParser()
assessment_parser.add_argument('title', type=str, required=True, help='Title is required')
assessment_parser.add_argument('description', type=str, required=False)
assessment_parser.add_argument('candidate_id', type=str, required=True, help='Candidate ID is required')

question_parser = reqparse.RequestParser()
question_parser.add_argument('text', type=str, required=True, help='Question text is required')
question_parser.add_argument('category', type=str, required=True, help='Question category is required')

class AssessmentResource(Resource):
    """Resource for managing assessments."""
    
    @login_required
    def get(self, assessment_id=None):
        """Get assessment(s)."""
        if assessment_id:
            # Get single assessment
            assessment = Assessment.objects.get_or_404(id=assessment_id)
            
            # Check permissions
            if not (current_user.is_admin or 
                   current_user.is_examiner or 
                   str(assessment.candidate_id) == str(current_user.id)):
                abort(403, message='You do not have permission to view this assessment')
                
            return assessment.to_dict()
        else:
            # Get all assessments (filtered by user role)
            if current_user.is_admin:
                assessments = Assessment.objects()
            elif current_user.is_examiner:
                assessments = Assessment.objects(examiner_id=current_user.id)
            else:
                assessments = Assessment.objects(candidate_id=current_user.id)
                
            return [a.to_dict() for a in assessments]
    
    @login_required
    @examiner_required
    def post(self):
        """Create a new assessment."""
        args = assessment_parser.parse_args()
        
        # Create new assessment
        assessment = Assessment(
            title=args['title'],
            description=args.get('description', ''),
            candidate_id=args['candidate_id'],
            examiner_id=current_user.id,
            status='draft'
        )
        
        assessment.save()
        return assessment.to_dict(), 201
    
    @login_required
    @examiner_required
    def put(self, assessment_id):
        """Update an assessment."""
        assessment = Assessment.objects.get_or_404(id=assessment_id)
        args = assessment_parser.parse_args()
        
        # Check permissions
        if not (current_user.is_admin or str(assessment.examiner_id) == str(current_user.id)):
            abort(403, message='You do not have permission to update this assessment')
        
        # Update fields
        assessment.title = args['title']
        assessment.description = args.get('description', assessment.description)
        assessment.updated_at = datetime.utcnow()
        
        assessment.save()
        return assessment.to_dict()
    
    @login_required
    @admin_required
    def delete(self, assessment_id):
        """Delete an assessment (admin only)."""
        assessment = Assessment.objects.get_or_404(id=assessment_id)
        assessment.delete()
        return {'message': 'Assessment deleted successfully'}, 200


class QuestionResource(Resource):
    """Resource for managing questions."""
    
    @login_required
    def get(self, assessment_id, question_id=None):
        """Get question(s) for an assessment."""
        assessment = Assessment.objects.get_or_404(id=assessment_id)
        
        # Check permissions
        if not (current_user.is_admin or 
               current_user.is_examiner or 
               str(assessment.candidate_id) == str(current_user.id)):
            abort(403, message='You do not have permission to view these questions')
        
        if question_id:
            # Get single question
            question = assessment.questions.filter(id=question_id).first_or_404()
            return question.to_dict()
        else:
            # Get all questions for assessment
            return [q.to_dict() for q in assessment.questions]
    
    @login_required
    @examiner_required
    def post(self, assessment_id):
        """Add a question to an assessment."""
        assessment = Assessment.objects.get_or_404(id=assessment_id)
        
        # Check permissions
        if not (current_user.is_admin or str(assessment.examiner_id) == str(current_user.id)):
            abort(403, message='You do not have permission to add questions to this assessment')
        
        args = question_parser.parse_args()
        
        # Create new question
        question = Question(
            text=args['text'],
            category=args['category'],
            created_by=current_user.id
        )
        
        assessment.questions.append(question)
        assessment.save()
        
        return question.to_dict(), 201


class AudioRecordingResource(Resource):
    """Resource for managing audio recordings."""
    
    @login_required
    def post(self, assessment_id, question_id):
        """Upload an audio recording for a question."""
        if 'audio' not in request.files:
            abort(400, message='No audio file provided')
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            abort(400, message='No selected file')
        
        # Get assessment and question
        assessment = Assessment.objects.get_or_404(id=assessment_id)
        question = assessment.questions.filter(id=question_id).first_or_404()
        
        # Check permissions
        if not (current_user.is_admin or 
               current_user.is_examiner or 
               str(assessment.candidate_id) == str(current_user.id)):
            abort(403, message='You do not have permission to add recordings to this assessment')
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}_{secure_filename(audio_file.filename)}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save the file
        audio_file.save(filepath)
        
        # Process the audio file (transcribe, analyze, etc.)
        try:
            transcription = process_audio_file(filepath)
            
            # Create audio recording
            recording = AudioRecording(
                file_path=filepath,
                file_name=audio_file.filename,
                mime_type=audio_file.mimetype,
                transcription=transcription,
                recorded_by=current_user.id
            )
            
            # Add recording to question
            question.recording = recording
            question.updated_at = datetime.utcnow()
            assessment.save()
            
            return recording.to_dict(), 201
            
        except Exception as e:
            # Clean up the file if processing fails
            if os.path.exists(filepath):
                os.remove(filepath)
            current_app.logger.error(f'Error processing audio file: {str(e)}')
            abort(500, message='Error processing audio file')


# Register API resources
def register_resources(api):
    """Register all API resources."""
    api.add_resource(AssessmentResource, 
                    '/assessments',
                    '/assessments/<string:assessment_id>')
                    
    api.add_resource(QuestionResource,
                    '/assessments/<string:assessment_id>/questions',
                    '/assessments/<string:assessment_id>/questions/<string:question_id>')
                    
    api.add_resource(AudioRecordingResource,
                    '/assessments/<string:assessment_id>/questions/<string:question_id>/recording')
