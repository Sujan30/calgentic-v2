import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface CommandBarProps {
  placeholder?: string;
  onSubmit?: (value: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const CommandBar = ({ 
  placeholder = "Type your request...", 
  onSubmit,
  isLoading = false,
  disabled = false
}: CommandBarProps) => {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSubmit && value.trim()) onSubmit(value);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className={`glass relative flex items-center bg-gray-100 dark:bg-white rounded-lg border border-gray-200 dark:border-gray-300 ${disabled ? 'opacity-70' : ''}`}>
        {isLoading ? (
          <Loader2 className="absolute left-4 text-primary animate-spin" size={20} />
        ) : (
          <Search className="absolute left-4 text-gray-400" size={20} />
        )}
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={isLoading ? "Processing..." : placeholder}
          className="w-full py-4 pl-12 pr-4 bg-transparent border-none focus:outline-none focus:ring-0 text-gray-800 placeholder-gray-400 **z-10 relative**" // ADDED z-10 AND relative
          disabled={isLoading || disabled}
        />
        {value.trim() && (
          <button
            type="submit"
            disabled={isLoading || disabled}
            className="absolute right-4 px-3 py-1 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {isLoading ? "Processing..." : "Send"}
          </button>
        )}
      </div>
    </form>
  );
};

export default CommandBar;