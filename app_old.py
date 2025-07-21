#!/usr/bin/env python3
"""
EP-Simulator - ICAO English Proficiency Assessment

This is the main application module that creates and configures the Flask application.
"""
import os
from flask import Flask
from config import config
from extensions import db

def create_app(config_name='default'):
    """Application factory function"""
    # Create and configure the Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    # Register routes
    from .auth import auth_bp
    from .main import main_bp
    from .api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Initialize database indexes
    with app.app_context():
        from .models import User, Assessment
        User.ensure_indexes()
        Assessment.ensure_indexes()
    
    # Configure upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Define routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.index'))
            return f'Welcome {current_user.name}! (Role: {current_user.role})'
        return redirect(url_for('auth.login'))

    @app.route('/admin')
    @login_required
    def admin_redirect():
        if current_user.role != 'admin':
            return "Access Denied", 403
        return redirect(url_for('admin.index'))

    @app.route('/')
    def index():
        """Admin dashboard"""
        return render_template('admin.html')

    @app.route('/candidate')
    def candidate():
        """Candidate assessment interface"""
        user_id = request.args.get('userId')
        if not user_id:
            return render_template('candidate.html')
        
        # Verify user exists
        user = User.objects(user_id=user_id).first()
        if not user:
            flash('Invalid user ID', 'error')
            return redirect(url_for('candidate'))
        
        # Get or create assessment
        assessment = Assessment.objects(user=user, status='in_progress').order_by('-start_time').first()
        if not assessment:
            assessment = Assessment(user=user)
            assessment.save()
        
        return render_template('candidate.html', user_id=user_id)

    @app.route('/api/start_session', methods=['POST'])
    def start_session():
        """Start a new assessment session"""
        data = request.json
        
        # Create new user
        user = User(
            user_id=generate_user_id(),
            first_name=data.get('firstName', '').strip(),
            last_name=data.get('lastName', '').strip(),
            email=data.get('email', '').strip(),
            phone=data.get('phone', '').strip()
        )
        user.save()
        
        # Create new assessment
        assessment = Assessment(user=user)
        assessment.save()
        
        return jsonify({
            'success': True,
            'userId': user.user_id,
            'assessmentId': str(assessment.id),
            'message': 'Session started successfully'
        })

    @app.route('/api/transcribe', methods=['POST'])
    def handle_audio():
        """Handle audio upload and transcription"""
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        user_id = request.form.get('userId')
        assessment_id = request.form.get('assessmentId')
        
        if not user_id or not assessment_id:
            return jsonify({'success': False, 'error': 'Missing user or assessment ID'}), 400
        
        # Verify user and assessment
        user = User.objects(user_id=user_id).first()
        assessment = Assessment.objects(id=assessment_id, user=user).first()
        
        if not user or not assessment:
            return jsonify({'success': False, 'error': 'Invalid user or assessment'}), 404
        
        # Save audio file
        audio_file = request.files['audio']
        filepath = save_audio_file(audio_file, user_id)
        
        if not filepath:
            return jsonify({'success': False, 'error': 'Failed to save audio file'}), 500
        
        # Transcribe audio
        result = transcribe_audio(filepath)
        
        if not result['success']:
            return jsonify({'success': False, 'error': result.get('error', 'Transcription failed')}), 500
        
        transcript = result['transcript']
        
        # Save recording to database
        recording = AudioRecording(
            assessment=assessment,
            file_path=filepath,
            transcript=transcript
        )
        recording.save()
        
        # Update assessment with recording
        if not assessment.recordings:
            assessment.recordings = []
        assessment.recordings.append({
            'recording_id': str(recording.id),
            'stage': assessment.current_stage,
            'timestamp': datetime.utcnow()
        })
        assessment.save()
        
        return jsonify({
            'success': True,
            'transcript': transcript,
            'recordingId': str(recording.id)
        })

    @app.route('/api/generate_questions', methods=['POST'])
    def generate_assessment_questions():
        """Generate follow-up questions based on transcript"""
        data = request.json
        transcript = data.get('transcript', '')
        context = data.get('context', '')
        
        if not transcript:
            return jsonify({'success': False, 'error': 'No transcript provided'}), 400
        
        # Generate questions using GPT
        result = generate_questions(transcript, context)
        
        if not result['success']:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to generate questions')}), 500
        
        return jsonify({
            'success': True,
            'questions': result['questions']
        })

    @app.route('/api/evaluate', methods=['POST'])
    def evaluate_assessment():
        """Evaluate assessment and generate scores"""
        data = request.json
        assessment_id = data.get('assessmentId')
        
        if not assessment_id:
            return jsonify({'success': False, 'error': 'No assessment ID provided'}), 400
        
        # Get assessment
        assessment = Assessment.objects(id=assessment_id).first()
        if not assessment:
            return jsonify({'success': False, 'error': 'Assessment not found'}), 404
        
        # Get all transcripts for this assessment
        recordings = AudioRecording.objects(assessment=assessment)
        full_transcript = "\n\n".join([r.transcript for r in recordings if r.transcript])
        
        if not full_transcript:
            return jsonify({'success': False, 'error': 'No transcripts available for evaluation'}), 400
        
        # Evaluate using GPT
        result = evaluate_response(full_transcript)
        
        if not result['success']:
            return jsonify({'success': False, 'error': result.get('error', 'Evaluation failed')}), 500
        
        # Update assessment with scores
        evaluation = result['evaluation']
        assessment.evaluation = evaluation
        assessment.scores = {k: v['score'] for k, v in evaluation.items() if k in Config.ASSESSMENT_CRITERIA}
        assessment.status = 'completed'
        assessment.end_time = datetime.utcnow()
        assessment.save()
    
    return app

# Import models after db initialization to avoid circular imports
with app.app_context():
    from models import User, Assessment, AudioRecording, Question

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def generate_user_id():
    """Generate a unique 6-character user ID"""
    while True:
        user_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not User.objects(user_id=user_id).first():
            return user_id

def save_audio_file(audio_file, user_id):
    """Save uploaded audio file and return its path"""
    if not audio_file:
        return None
        
    # Create user directory if it doesn't exist
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    filename = f"{uuid.uuid4().hex}.wav"
    filepath = os.path.join(user_dir, filename)
    
    # Save file
    audio_file.save(filepath)
    
    return filepath

# Routes
@app.route('/')
def index():
    """Admin dashboard"""
    return render_template('admin.html')

@app.route('/candidate')
def candidate():
    """Candidate assessment interface"""
    user_id = request.args.get('userId')
    if not user_id:
        return render_template('candidate.html')
    
    # Verify user exists
    user = User.objects(user_id=user_id).first()
    if not user:
        flash('Invalid user ID', 'error')
        return redirect(url_for('candidate'))
    
    # Get or create assessment
    assessment = Assessment.objects(user=user, status='in_progress').order_by('-start_time').first()
    if not assessment:
        assessment = Assessment(user=user)
        assessment.save()
    
    return render_template('candidate.html', user_id=user_id)

# API Endpoints
@app.route('/api/start_session', methods=['POST'])
def start_session():
    """Start a new assessment session"""
    data = request.json
    
    # Create new user
    user = User(
        user_id=generate_user_id(),
        first_name=data.get('firstName', '').strip(),
        last_name=data.get('lastName', '').strip(),
        email=data.get('email', '').strip(),
        phone=data.get('phone', '').strip()
    )
    user.save()
    
    # Create new assessment
    assessment = Assessment(user=user)
    assessment.save()
    
    return jsonify({
        'success': True,
        'userId': user.user_id,
        'assessmentId': str(assessment.id),
        'message': 'Session started successfully'
    })

@app.route('/api/transcribe', methods=['POST'])
def handle_audio():
    """Handle audio upload and transcription"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file provided'}), 400
    
    user_id = request.form.get('userId')
    assessment_id = request.form.get('assessmentId')
    
    if not user_id or not assessment_id:
        return jsonify({'success': False, 'error': 'Missing user or assessment ID'}), 400
    
    # Verify user and assessment
    user = User.objects(user_id=user_id).first()
    assessment = Assessment.objects(id=assessment_id, user=user).first()
    
    if not user or not assessment:
        return jsonify({'success': False, 'error': 'Invalid user or assessment'}), 404
    
    # Save audio file
    audio_file = request.files['audio']
    filepath = save_audio_file(audio_file, user_id)
    
    if not filepath:
        return jsonify({'success': False, 'error': 'Failed to save audio file'}), 500
    
    # Transcribe audio
    result = transcribe_audio(filepath)
    
    if not result['success']:
        return jsonify({'success': False, 'error': result.get('error', 'Transcription failed')}), 500
    
    transcript = result['transcript']
    
    # Save recording to database
    recording = AudioRecording(
        assessment=assessment,
        file_path=filepath,
        transcript=transcript
    )
    recording.save()
    
    # Update assessment with recording
    if not assessment.recordings:
        assessment.recordings = []
    assessment.recordings.append({
        'recording_id': str(recording.id),
        'stage': assessment.current_stage,
        'timestamp': datetime.utcnow()
    })
    assessment.save()
    
    return jsonify({
        'success': True,
        'transcript': transcript,
        'recordingId': str(recording.id)
    })

@app.route('/api/generate_questions', methods=['POST'])
def generate_assessment_questions():
    """Generate follow-up questions based on transcript"""
    data = request.json
    transcript = data.get('transcript', '')
    context = data.get('context', '')
    
    if not transcript:
        return jsonify({'success': False, 'error': 'No transcript provided'}), 400
    
    # Generate questions using GPT
    result = generate_questions(transcript, context)
    
    if not result['success']:
        return jsonify({'success': False, 'error': result.get('error', 'Failed to generate questions')}), 500
    
    return jsonify({
        'success': True,
        'questions': result['questions']
    })

@app.route('/api/evaluate', methods=['POST'])
def evaluate_assessment():
    """Evaluate assessment and generate scores"""
    data = request.json
    assessment_id = data.get('assessmentId')
    
    if not assessment_id:
        return jsonify({'success': False, 'error': 'No assessment ID provided'}), 400
    
    # Get assessment
    assessment = Assessment.objects(id=assessment_id).first()
    if not assessment:
        return jsonify({'success': False, 'error': 'Assessment not found'}), 404
    
    # Get all transcripts for this assessment
    recordings = AudioRecording.objects(assessment=assessment)
    full_transcript = "\n\n".join([r.transcript for r in recordings if r.transcript])
    
    if not full_transcript:
        return jsonify({'success': False, 'error': 'No transcripts available for evaluation'}), 400
    
    # Evaluate using GPT
    result = evaluate_response(full_transcript)
    
    if not result['success']:
        return jsonify({'success': False, 'error': result.get('error', 'Evaluation failed')}), 500
    
    # Update assessment with scores
    evaluation = result['evaluation']
    assessment.evaluation = evaluation
    assessment.scores = {k: v['score'] for k, v in evaluation.items() if k in Config.ASSESSMENT_CRITERIA}
    assessment.status = 'completed'
    assessment.end_time = datetime.utcnow()
    assessment.save()
    
    return jsonify({
        'success': True,
        'scores': assessment.scores,
        'evaluation': evaluation
    })

@app.route('/api/assessment/<assessment_id>')
def get_assessment(assessment_id):
    """Get assessment details"""
    assessment = Assessment.objects(id=assessment_id).first()
    if not assessment:
        return jsonify({'success': False, 'error': 'Assessment not found'}), 404
    
    return jsonify({
        'success': True,
        'assessment': {
            'id': str(assessment.id),
            'userId': assessment.user.user_id,
            'status': assessment.status,
            'startTime': assessment.start_time.isoformat(),
            'endTime': assessment.end_time.isoformat() if assessment.end_time else None,
            'scores': assessment.scores,
            'overallScore': assessment.calculate_overall_score()
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'success': False, 'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create database indexes
    with app.app_context():
        User.ensure_indexes()
        Assessment.ensure_indexes()
        Question.ensure_indexes()
        AudioRecording.ensure_indexes()
    
    # Create default questions if none exist
    if Question.objects.count() == 0:
        default_questions = [
            {
                'text': 'Can you describe your experience as a pilot?',
                'category': 'introduction',
                'difficulty': 3
            },
            {
                'text': 'What do you see in this picture?',
                'category': 'picture',
                'difficulty': 2
            },
            {
                'text': 'Describe how you would handle an engine failure after takeoff.',
                'category': 'scenario',
                'difficulty': 4
            }
        ]
        
        for q in default_questions:
            Question(**q).save()
    
    # Run the application
    app.run(debug=True, port=5000)
