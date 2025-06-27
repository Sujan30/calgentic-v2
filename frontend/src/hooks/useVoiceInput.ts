import { useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';

interface UseVoiceInputProps {
  onTranscription: (text: string) => void;
  isAuthenticated: boolean;
}

interface UseVoiceInputReturn {
  isListening: boolean;
  isLoading: boolean;
  startListening: () => void;
  stopListening: () => void;
  error: string | null;
}

export const useVoiceInput = ({ onTranscription, isAuthenticated }: UseVoiceInputProps): UseVoiceInputReturn => {
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  const startListening = useCallback(async () => {
    if (!isAuthenticated) {
      toast.error('Please sign in to use voice input');
      return;
    }

    try {
      setError(null);
      setIsLoading(true);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      const audioChunks: Blob[] = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
        const reader = new FileReader();
        
        reader.onloadend = async () => {
          try {
            const base64Audio = (reader.result as string).split(',')[1];
            
            const response = await fetch('/api/transcribe', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              credentials: 'include',
              body: JSON.stringify({
                audioData: base64Audio,
                audioFormat: 'WEBM_OPUS'
              })
            });
            
            const result = await response.json();
            
            if (response.ok && result.transcription) {
              onTranscription(result.transcription);
            } else {
              setError(result.error || 'Transcription failed');
              toast.error(result.error || 'Transcription failed');
            }
          } catch (err) {
            setError('Failed to process transcription');
            toast.error('Failed to process transcription');
          } finally {
            setIsLoading(false);
          }
        };
        
        reader.readAsDataURL(audioBlob);
      };
      
      recognitionRef.current = mediaRecorder;
      setIsListening(true);
      setIsLoading(false);
      
      mediaRecorder.start();
      
    } catch (err) {
      setIsLoading(false);
      
      if (err instanceof Error && err.name === 'NotAllowedError') {
        setError('Microphone access denied. Please allow microphone permissions.');
        toast.error('Microphone access denied. Please allow microphone permissions.');
      } else {
        setError('Failed to access microphone. Please try again.');
        toast.error('Failed to access microphone. Please try again.');
      }
    }
  }, [isAuthenticated, onTranscription]);

  const stopListening = useCallback(() => {
    setIsListening(false);
    if (recognitionRef.current && recognitionRef.current.state !== 'inactive') {
      recognitionRef.current.stop();
    }
  }, []);

  return {
    isListening,
    isLoading,
    startListening,
    stopListening,
    error
  };
};
