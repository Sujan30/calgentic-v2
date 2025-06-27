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
      stream.getTracks().forEach(track => track.stop());

      setIsListening(true);
      setIsLoading(false);
      
      setTimeout(() => {
        const mockTranscription = "Schedule a meeting tomorrow at 2pm";
        onTranscription(mockTranscription);
        stopListening();
      }, 3000);

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
    setIsLoading(false);
    if (recognitionRef.current) {
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
