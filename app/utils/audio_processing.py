"""
Audio Processing Utilities

This module contains functions for processing audio files, including:
- Transcribing speech to text
- Analyzing audio quality
- Extracting features
"""
import os
import tempfile
import logging
from pydub import AudioSegment
import speech_recognition as sr
import librosa
import numpy as np
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_to_wav(audio_path: str) -> str:
    """
    Convert an audio file to WAV format if it's not already.
    
    Args:
        audio_path: Path to the input audio file
        
    Returns:
        Path to the converted WAV file
    """
    if audio_path.lower().endswith('.wav'):
        return audio_path
        
    try:
        # Create a temporary file for the WAV output
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav.close()
        
        # Convert to WAV using pydub
        audio = AudioSegment.from_file(audio_path)
        audio.export(temp_wav.name, format='wav')
        
        return temp_wav.name
        
    except Exception as e:
        logger.error(f"Error converting audio to WAV: {str(e)}")
        raise

def transcribe_audio(audio_path: str, language: str = 'en-US') -> str:
    """
    Transcribe speech from an audio file to text.
    
    Args:
        audio_path: Path to the audio file
        language: Language code for transcription (default: 'en-US')
        
    Returns:
        Transcribed text
    """
    try:
        # Convert to WAV if needed
        wav_path = convert_to_wav(audio_path)
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Read audio file
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            
            try:
                # Use Google Web Speech API for transcription
                text = recognizer.recognize_google(audio_data, language=language)
                return text
                
            except sr.UnknownValueError:
                logger.warning("Google Speech Recognition could not understand audio")
                return ""
            except sr.RequestError as e:
                logger.error(f"Could not request results from Google Speech Recognition service; {e}")
                return ""
                
    except Exception as e:
        logger.error(f"Error in transcription: {str(e)}")
        return ""
    finally:
        # Clean up temporary WAV file if it was created
        if 'wav_path' in locals() and wav_path != audio_path and os.path.exists(wav_path):
            os.unlink(wav_path)

def analyze_audio_quality(audio_path: str) -> Dict[str, Any]:
    """
    Analyze audio quality metrics.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Dictionary containing audio quality metrics
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=None)
        
        # Calculate metrics
        duration = librosa.get_duration(y=y, sr=sr)
        rms = np.sqrt(np.mean(y**2))  # Root Mean Square (loudness)
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        
        # Zero crossing rate (noisiness)
        zero_crossings = np.mean(librosa.feature.zero_crossing_rate(y))
        
        # Silence detection
        non_silent_ranges = librosa.effects.split(y, top_db=30)
        silence_duration = duration - sum(end - start for start, end in non_silent_ranges) / sr
        
        return {
            'duration_seconds': float(duration),
            'sample_rate': int(sr),
            'rms': float(rms),
            'spectral_centroid_mean': float(np.mean(spectral_centroids)),
            'spectral_bandwidth_mean': float(np.mean(spectral_bandwidth)),
            'zero_crossing_rate': float(zero_crossings),
            'silence_duration_seconds': float(silence_duration),
            'speech_duration_seconds': float(duration - silence_duration)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing audio quality: {str(e)}")
        return {}

def extract_audio_features(audio_path: str) -> Dict[str, Any]:
    """
    Extract various audio features for analysis.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Dictionary containing audio features
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=None)
        
        # Calculate various audio features
        features = {}
        
        # Basic features
        features['duration'] = float(librosa.get_duration(y=y, sr=sr))
        features['sample_rate'] = int(sr)
        
        # Temporal features
        features['rms_energy'] = float(np.sqrt(np.mean(y**2)))
        features['zero_crossing_rate'] = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        
        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        features['spectral_centroid_mean'] = float(np.mean(spectral_centroid))
        features['spectral_centroid_std'] = float(np.std(spectral_centroid))
        
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        features['spectral_bandwidth_mean'] = float(np.mean(spectral_bandwidth))
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        features['spectral_rolloff_mean'] = float(np.mean(spectral_rolloff))
        
        # MFCCs (Mel-frequency cepstral coefficients)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        for i, mfcc in enumerate(mfccs):
            features[f'mfcc_{i+1}_mean'] = float(np.mean(mfcc))
            features[f'mfcc_{i+1}_std'] = float(np.std(mfcc))
        
        # Chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features['chroma_mean'] = float(np.mean(chroma))
        features['chroma_std'] = float(np.std(chroma))
        
        # Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)
        features['mel_spectrogram_mean'] = float(np.mean(mel_spec))
        
        return features
        
    except Exception as e:
        logger.error(f"Error extracting audio features: {str(e)}")
        return {}

def analyze_pronunciation(audio_path: str, reference_text: str, language: str = 'en-US') -> Dict[str, Any]:
    """
    Analyze pronunciation quality by comparing audio to reference text.
    
    Args:
        audio_path: Path to the audio file
        reference_text: The expected text that was spoken
        language: Language code for analysis (default: 'en-US')
        
    Returns:
        Dictionary containing pronunciation analysis results
    """
    try:
        # Transcribe the audio
        transcription = transcribe_audio(audio_path, language=language)
        
        # Simple word error rate calculation
        ref_words = set(reference_text.lower().split())
        trans_words = set(transcription.lower().split())
        
        # Calculate word error rate (simplified)
        correct_words = ref_words.intersection(trans_words)
        total_words = len(ref_words.union(trans_words))
        wer = 1 - (len(correct_words) / total_words) if total_words > 0 else 1.0
        
        # Basic pronunciation score (0-100 scale)
        pronunciation_score = max(0, 100 * (1 - wer))
        
        return {
            'transcription': transcription,
            'word_error_rate': float(wer),
            'pronunciation_score': float(pronunciation_score),
            'correct_words': list(correct_words),
            'missing_words': list(ref_words - trans_words),
            'extra_words': list(trans_words - ref_words)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing pronunciation: {str(e)}")
        return {}

def process_audio_file(audio_path: str) -> Dict[str, Any]:
    """
    Process an audio file and return analysis results.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Dictionary containing transcription and analysis results
    """
    # Transcribe the audio
    transcription = transcribe_audio(audio_path)
    
    # Analyze audio quality
    quality_metrics = analyze_audio_quality(audio_path)
    
    # Extract audio features
    audio_features = extract_audio_features(audio_path)
    
    return {
        'transcription': transcription,
        'quality_metrics': quality_metrics,
        'audio_features': audio_features,
        'word_count': len(transcription.split()) if transcription else 0,
        'language': 'en-US'  # Default language, can be made configurable
    }
