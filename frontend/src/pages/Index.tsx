import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import CommandBar from '@/components/CommandBar';
import { Calendar, Clock, ArrowRight, CheckCircle, Sparkles, Zap, Users } from 'lucide-react';
import { sendPrompt, CalendarResponse } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';

const Index = () => {
  const [response, setResponse] = useState<CalendarResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const navigate = useNavigate();

  // Check authentication status
  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/check-auth`, {
        method: "GET",
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setIsAuthenticated(data.authenticated || false);
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error("Auth check error:", error);
      setIsAuthenticated(false);
    } finally {
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handlePromptSubmit = async (prompt: string) => {
    if (!isAuthenticated) {
      toast.error("Please sign in to use the calendar assistant");
      navigate('/login');
      return;
    }

    if (!prompt.trim()) return;
    
    setIsLoading(true);
    
    try {
      const result = await sendPrompt(prompt);
      
      setResponse(result);
      
      if (result.error) {
        toast.error(result.error);
        console.error("Error from server:", result.error);
      } else if (result.message) {
        toast.success("Request processed successfully!");
      }
    } catch (error) {
      console.error("Error processing request:", error);
      if (error instanceof Error) {
        toast.error(`Error: ${error.message}`);
      } else {
        toast.error("Failed to process your request. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-black">
      <Header />
      
      {/* Hero Section */}
      <section className="pt-32 section-padding pb-20">
        <div className="max-w-7xl mx-auto text-center animate-fade-up">
          <div className="inline-flex items-center justify-center p-2 mb-6 rounded-full bg-primary/10 text-primary">
            <Sparkles className="w-5 h-5 mr-2" />
            <span className="text-sm font-medium">AI-Powered Calendar Management</span>
          </div>
          
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 dark:text-white mb-6 tracking-tight">
            Your Smart Calendar
            <span className="block text-primary">Assistant</span>
          </h1>
          
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
            Transform how you manage your schedule with natural language commands. 
            Create events, and organize your calendar effortlessly.
          </p>
          
          {!authLoading && (
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button size="lg" className="gap-2">
                    <Calendar className="w-5 h-5" />
                    Go to Dashboard
                  </Button>
                </Link>
              ) : (
                <Link to="/login">
                  <Button size="lg" className="gap-2">
                    <Calendar className="w-5 h-5" />
                    Get Started
                  </Button>
                </Link>
              )}
              
              <Link to="/about">
                <Button variant="outline" size="lg" className="gap-2">
                  Learn More
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Interactive Demo Section */}
      <section className="section-padding bg-gray-50 dark:bg-gray-900/50">
        <div className="max-w-4xl mx-auto animate-fade-up">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Try CalGentic Now
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-300">
              Experience the power of natural language calendar management
            </p>
          </div>
          
          <div className="glass p-6 text-left">
            <CommandBar 
              placeholder='Try "Schedule a meeting with John at 3 PM tomorrow" or "What events do I have this week?"'
              onSubmit={handlePromptSubmit}
              isLoading={isLoading}
              isAuthenticated={isAuthenticated}
            />
            
            {!isAuthenticated && !authLoading && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-3 text-center">
                Sign in to actually create and manage calendar events
              </p>
            )}
            
            {/* Quick examples */}
            {!response && !isLoading && (
              <div className="flex flex-wrap justify-center gap-3 mt-6 text-sm text-gray-500 dark:text-gray-300">
                <span className="glass px-3 py-1 cursor-pointer hover:bg-white/20 dark:hover:bg-black/40 transition"
                  onClick={() => handlePromptSubmit("What events do I have today?")}>
                  "What events do I have today?"
                </span>
                <span className="glass px-3 py-1 cursor-pointer hover:bg-white/20 dark:hover:bg-black/40 transition"
                  onClick={() => handlePromptSubmit("Schedule a team meeting tomorrow at 10am")}>
                  "Schedule a team meeting tomorrow at 10am"
                </span>
                <span className="glass px-3 py-1 cursor-pointer hover:bg-white/20 dark:hover:bg-black/40 transition"
                  onClick={() => handlePromptSubmit("I have a meeting with sujan for next monday at 10am")}>
                  "I have a meeting with sujan for next monday at 10am"
                </span>
              </div>
            )}
          </div>
          
          {/* Response Display */}
          {response && (
            <div className="mt-6 animate-fade-up">
              {response.message && (
                <div className="glass p-6 text-left">
                  <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">Response</h3>
                  <p className="text-gray-800 dark:text-gray-200">{response.message}</p>
                  
                  <div className="mt-4">
                    <Button 
                      onClick={() => setResponse(null)} 
                      variant="outline"
                      className="glass hover:bg-white/20 dark:hover:bg-black/40 transition"
                    >
                      Try Another Command
                    </Button>
                  </div>
                </div>
              )}
              
              {response.events && response.events.length > 0 && (
                <div className="glass p-6 text-left mt-4">
                  <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Events Found</h3>
                  <div className="space-y-3">
                    {response.events.map((event, index) => (
                      <div key={index} className="glass p-4">
                        <h4 className="font-medium text-gray-900 dark:text-white">{event.summary}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{event.description}</p>
                        <div className="flex items-center mt-2 text-sm text-gray-600 dark:text-gray-300">
                          <Clock className="w-4 h-4 mr-1" />
                          <span>
                            {new Date(event.start).toLocaleString()} - {new Date(event.end).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4">
                    <Button 
                      onClick={() => setResponse(null)} 
                      variant="outline"
                      className="glass hover:bg-white/20 dark:hover:bg-black/40 transition"
                    >
                      Try Another Command
                    </Button>
                  </div>
                </div>
              )}
              
              {response.error && (
                <div className="glass p-6 text-left mt-4 bg-red-50 dark:bg-red-900/20">
                  <h3 className="text-lg font-semibold mb-2 text-red-700 dark:text-red-400">Error</h3>
                  <p className="text-red-600 dark:text-red-300">{response.error}</p>
                  
                  <div className="mt-4">
                    <Button 
                      onClick={() => setResponse(null)} 
                      variant="outline"
                      className="glass hover:bg-white/20 dark:hover:bg-black/40 transition"
                    >
                      Try Again
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="section-padding">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 animate-fade-up">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Why Choose CalGentic?
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Experience the future of calendar management with our AI-powered assistant
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="glass p-6 text-left animate-fade-up" style={{animationDelay: '0.1s'}}>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Natural Language Processing
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Just type what you want in plain English. No complex forms or confusing interfaces.
              </p>
            </div>
            
            <div className="glass p-6 text-left animate-fade-up" style={{animationDelay: '0.2s'}}>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <Calendar className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Google Calendar Integration
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Seamlessly syncs with your existing Google Calendar. All your events in one place.
              </p>
            </div>
            
            <div className="glass p-6 text-left animate-fade-up" style={{animationDelay: '0.3s'}}>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <CheckCircle className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Smart Scheduling
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                AI understands context and suggests optimal times based on your existing schedule.
              </p>
            </div>
          </div>
        </div>
      </section>
      <Footer/>
    </div>
  );
};

export default Index;
