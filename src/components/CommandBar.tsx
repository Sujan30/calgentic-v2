
import React from 'react';
import { Search } from 'lucide-react';

interface CommandBarProps {
  placeholder?: string;
  onSubmit?: (value: string) => void;
}

const CommandBar = ({ placeholder = "Type your request...", onSubmit }: CommandBarProps) => {
  const [value, setValue] = React.useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSubmit) onSubmit(value);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className="glass relative flex items-center">
        <Search className="absolute left-4 text-gray-400" size={20} />
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          className="w-full py-4 pl-12 pr-4 bg-transparent border-none focus:outline-none focus:ring-0 text-gray-800 placeholder-gray-400"
        />
      </div>
    </form>
  );
};

export default CommandBar;
