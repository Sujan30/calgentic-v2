import React, { useState } from 'react';
import { Search, Loader2, Mic, MicOff } from 'lucide-react';
import { useVoiceInput } from '@/hooks/useVoiceInput';

interface CommandBarProps {
  placeholder?: string;
  onSubmit?: (value: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  isAuthenticated?: boolean;
}

const CommandBar = ({ 
  placeholder = "Type your request...", 
  onSubmit,
  isLoading = false,
  disabled = false,
  isAuthenticated = false
}: CommandBarProps) => {
  const [value, setValue] = useState("");

  const handleVoiceTranscription = (transcription: string) => {
    setValue(transcription);
    if (onSubmit && transcription.trim()) {
      onSubmit(transcription);
    }
  };

  const {
    isListening,
    isLoading: voiceLoading,
    startListening,
    stopListening
  } = useVoiceInput({
    onTranscription: handleVoiceTranscription,
    isAuthenticated
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSubmit && value.trim()) onSubmit(value);
  };

  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const isProcessing = isLoading || voiceLoading;

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className={`glass relative flex items-center bg-gray-100 dark:bg-white rounded-lg border border-gray-200 dark:border-gray-300 ${disabled ? 'opacity-70' : ''}`}>
        {isProcessing ? (
          <Loader2 className="absolute left-4 text-primary animate-spin" size={20} />
        ) : (
          <Search className="absolute left-4 text-gray-400" size={20} />
        )}
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={isProcessing ? "Processing..." : (isListening ? "Listening..." : placeholder)}
          className="w-full py-4 pl-12 pr-20 bg-transparent border-none focus:outline-none focus:ring-0 text-gray-800 placeholder-gray-400"
          disabled={isProcessing || disabled}
        />
        
        {isAuthenticated && (
          <button
            type="button"
            onClick={handleVoiceToggle}
            disabled={isProcessing || disabled}
            className={`absolute right-16 p-2 rounded-md transition-colors ${
              isListening 
                ? 'text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20' 
                : 'text-gray-400 hover:text-primary hover:bg-gray-50 dark:hover:bg-gray-800'
            } disabled:opacity-50`}
            title={isListening ? "Stop listening" : "Start voice input"}
          >
            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
        )}
        
        {value.trim() && (
          <button
            type="submit"
            disabled={isProcessing || disabled}
            className="absolute right-4 px-3 py-1 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {isProcessing ? "Processing..." : "Send"}
          </button>
        )}
      </div>
    </form>
  );
};

export default CommandBar;
