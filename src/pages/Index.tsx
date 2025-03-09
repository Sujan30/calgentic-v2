import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import CommandBar from '@/components/CommandBar';
import { Calendar, Clock, ArrowUp, ArrowRight } from 'lucide-react';
import { sendPrompt, CalendarResponse } from '@/lib/api';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';

const SubmitButton = () => {
  return (
    <button className="ml-2 p-3 bg-primary text-white rounded-lg shadow-md hover:bg-primary-dark transition flex items-center justify-center">
      <ArrowUp className="w-5 h-5" />
    </button>
  );
};

const Index = () => {
  const [response, setResponse] = useState<CalendarResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const handlePromptSubmit = async (prompt: string) => {
    if (!prompt.trim()) return;
    
    if (!isAuthenticated) {
      toast.error("Please sign in to use this feature");
      return;
    }
    
    setIsLoading(true);
    
    try {
      const result = await sendPrompt(prompt);
      
      setResponse(result);
      
      if (result.error) {
        toast.error(result.error);
      } else if (result.message) {
        toast.success("Request processed successfully!");
      }
    } catch (error) {
      toast.error("Failed to process your request. Please try again.");
      console.error("Error processing request:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-black">
      <Header />
      
      <main className="pt-32 section-padding pb-20">
        {/* Hero Section */}
        <div className="max-w-4xl mx-auto text-center animate-fade-up">
          <div className="inline-flex items-center justify-center p-2 mb-8 rounded-full bg-primary/10 text-primary">
            <Calendar className="w-5 h-5 mr-2" />
            <span className="text-sm font-medium">AI-Powered Calendar Assistant</span>
          </div>
          
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white mb-6 tracking-tight">
            Manage your schedule effortlessly with AI—just type your request
          </h1>
          
          <p className="text-lg text-gray-600 dark:text-gray-300 mb-12 max-w-2xl mx-auto">
            Schedule meetings, check availability, and manage your calendar using natural language. Let AI handle the complexity.
          </p>

          <div className="space-y-8">
            <CommandBar 
              placeholder={isAuthenticated 
                ? 'Try "Schedule a meeting with John at 3 PM tomorrow"' 
                : 'Sign in to start using AI calendar assistant'}
              onSubmit={handlePromptSubmit}
              isLoading={isLoading}
              disabled={!isAuthenticated && !authLoading}
            />
            
            {!isAuthenticated && !authLoading && (
              <div className="mt-6">
                <Button 
                  onClick={() => navigate('/login')} 
                  className="gap-2"
                  size="lg"
                >
                  Sign in to get started
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            )}
            
            {isAuthenticated && !isLoading && !response && (
              <div className="mt-6">
                <Button 
                  onClick={() => navigate('/dashboard')} 
                  className="gap-2"
                  size="lg"
                >
                  Go to Dashboard
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            )}
            
            {!response && !isLoading && isAuthenticated && (
              <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-500 dark:text-gray-300">
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
            )}
            
            {/* Response Display */}
            {response && (
              <div className="mt-8 animate-fade-up">
                {response.message && (
                  <div className="glass p-6 text-left max-w-2xl mx-auto text-gray-800 dark:text-white">
                    <h2 className="text-xl font-semibold mb-2 text-gray-800 dark:text-white">Response</h2>
                    <p>{response.message}</p>
                  </div>
                )}
                
                {response.events && response.events.length > 0 && (
                  <div className="glass p-6 text-left max-w-2xl mx-auto mt-4 text-gray-800 dark:text-white">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">Events</h2>
                    <div className="space-y-4">
                      {response.events.map((event, index) => (
                        <div key={index} className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
                          <h3 className="font-medium text-gray-900 dark:text-white">{event.summary}</h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{event.description}</p>
                          <div className="flex items-center mt-2 text-sm text-gray-600 dark:text-gray-300">
                            <Clock className="w-4 h-4 mr-1" />
                            <span>
                              {new Date(event.start).toLocaleString()} - {new Date(event.end).toLocaleString()}
                            </span>
                          </div>
                          {event.link && (
                            <a 
                              href={event.link} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-sm text-primary hover:underline mt-2 inline-block"
                            >
                              View in Calendar
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {response.error && (
                  <div className="glass p-6 text-left max-w-2xl mx-auto bg-red-50 dark:bg-red-900/20">
                    <h2 className="text-xl font-semibold mb-2 text-red-700 dark:text-red-400">Error</h2>
                    <p className="text-red-600 dark:text-red-300">{response.error}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
