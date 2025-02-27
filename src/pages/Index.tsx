
import React from 'react';
import Header from '@/components/Header';
import CommandBar from '@/components/CommandBar';
import { Calendar } from 'lucide-react';

const Index = () => {
  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-white to-gray-50">
      <Header />
      
      <main className="pt-32 section-padding">
        {/* Hero Section */}
        <div className="max-w-4xl mx-auto text-center animate-fade-up">
          <div className="inline-flex items-center justify-center p-2 mb-8 rounded-full bg-primary/10 text-primary">
            <Calendar className="w-5 h-5 mr-2" />
            <span className="text-sm font-medium">AI-Powered Calendar Assistant</span>
          </div>
          
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6 tracking-tight">
            Manage your schedule effortlessly with AI—just type your request
          </h1>
          
          <p className="text-lg text-gray-600 mb-12 max-w-2xl mx-auto">
            Schedule meetings, check availability, and manage your calendar using natural language. Let AI handle the complexity.
          </p>

          <div className="space-y-8">
            <CommandBar placeholder='Try "Schedule a meeting with John at 3 PM tomorrow"' />
            
            <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-500">
              <span className="glass px-3 py-1">
                "What events do I have this Friday?"
              </span>
              <span className="glass px-3 py-1">
                "Move my 2 PM meeting to 4 PM"
              </span>
              <span className="glass px-3 py-1">
                "Find a time next week for coffee with Sarah"
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
