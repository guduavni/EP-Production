import openai
import os
from config import Config
from datetime import datetime

# Configure OpenAI
openai.api_key = Config.OPENAI_API_KEY

def transcribe_audio(audio_file_path):
    """
    Transcribe audio using OpenAI Whisper
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )
        return response['text']
    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        return None

def generate_questions(transcript, context=None, num_questions=3):
    """
    Generate follow-up questions based on the transcript using GPT-4
    """
    try:
        prompt = f"""Based on the following transcript, generate {num_questions} relevant follow-up questions:
        
        Transcript: {transcript}
        
        Context: {context or 'No specific context provided'}
        
        Questions (one per line):"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates relevant follow-up questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.7,
        )
        
        questions = response.choices[0].message['content'].strip().split('\n')
        questions = [q.strip() for q in questions if q.strip()]
        
        return questions[:num_questions]  # Return only the requested number of questions
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        return []

def evaluate_response(transcript, criteria=None):
    """
    Evaluate the response based on ICAO language proficiency criteria
    """
    if criteria is None:
        criteria = {
            'pronunciation': "Assess the pronunciation, stress, rhythm, and intonation",
            'structure': "Evaluate the accuracy and variety of grammatical structures",
            'vocabulary': "Assess the range and appropriateness of vocabulary",
            'fluency': "Evaluate the flow, speed, and coherence of speech",
            'comprehension': "Assess the understanding of questions and responses",
            'interaction': "Evaluate the ability to maintain and develop the conversation"
        }
    
    try:
        prompt = f"""Evaluate the following pilot's response based on ICAO language proficiency criteria (scale 1-6, where 6 is expert level):
        
        Response: {transcript}
        
        Provide scores and brief justifications for each criterion:"""
        
        for criterion, description in criteria.items():
            prompt += f"\n- {criterion.capitalize()}: {description}"
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an ICAO language proficiency rater. Evaluate the response objectively."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.3,
        )
        
        evaluation = response.choices[0].message['content'].strip()
        
        # Extract scores (this is a simple implementation, you might want to make it more robust)
        scores = {}
        for line in evaluation.split('\n'):
            if ':' in line:
                criterion, score_text = line.split(':', 1)
                criterion = criterion.strip().lower()
                # Extract the first number in the score text
                for word in score_text.split():
                    try:
                        score = float(word)
                        if 1 <= score <= 6:  # ICAO levels are 1-6
                            scores[criterion] = score
                            break
                    except (ValueError, AttributeError):
                        pass
        
        overall_score = sum(scores.values()) / len(scores) if scores else 0
        return {
            'evaluation': evaluation,
            'scores': scores,
            'overall_score': round(overall_score, 1)
        }
    except Exception as e:
        print(f"Error in evaluation: {str(e)}")
        return {
            'evaluation': f"Error during evaluation: {str(e)}",
            'scores': {},
            'overall_score': 0
        }
