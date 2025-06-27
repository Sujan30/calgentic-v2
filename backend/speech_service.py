import os
import base64
import io
from google.cloud import speech
from google.api_core import exceptions
import logging

logger = logging.getLogger(__name__)

class SpeechTranscriptionService:
    def __init__(self):
        """Initialize Google Cloud Speech-to-Text client"""
        try:
            self.client = speech.SpeechClient()
        except Exception as e:
            logger.error(f"Failed to initialize Speech client: {e}")
            self.client = None
    
    def transcribe_audio(self, audio_data_base64: str, audio_format: str = "WEBM_OPUS") -> dict:
        """
        Transcribe audio data using Google Speech-to-Text API
        
        Args:
            audio_data_base64: Base64 encoded audio data
            audio_format: Audio encoding format (default: WEBM_OPUS)
            
        Returns:
            dict: Transcription result with text and confidence
        """
        if not self.client:
            return {
                "success": False,
                "error": "Speech client not initialized. Check Google Cloud credentials."
            }
        
        try:
            audio_data = base64.b64decode(audio_data_base64)
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            encoding_map = {
                "WEBM_OPUS": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "OGG_OPUS": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                "LINEAR16": speech.RecognitionConfig.AudioEncoding.LINEAR16,
                "FLAC": speech.RecognitionConfig.AudioEncoding.FLAC
            }
            
            encoding = encoding_map.get(audio_format, speech.RecognitionConfig.AudioEncoding.WEBM_OPUS)
            
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=48000,
                language_code="en-US",
                enable_automatic_punctuation=True,
                model="latest_long"
            )
            
            response = self.client.recognize(config=config, audio=audio)
            
            if not response.results:
                return {
                    "success": True,
                    "transcription": "",
                    "confidence": 0.0,
                    "message": "No speech detected in audio"
                }
            
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return {
                "success": True,
                "transcription": alternative.transcript,
                "confidence": alternative.confidence,
                "message": "Transcription successful"
            }
            
        except exceptions.InvalidArgument as e:
            logger.error(f"Invalid audio format or configuration: {e}")
            return {
                "success": False,
                "error": f"Invalid audio format: {str(e)}"
            }
        except exceptions.DeadlineExceeded as e:
            logger.error(f"Speech API timeout: {e}")
            return {
                "success": False,
                "error": "Transcription timeout. Please try with shorter audio."
            }
        except Exception as e:
            logger.error(f"Speech transcription error: {e}")
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
            }
