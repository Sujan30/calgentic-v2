import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import CommandBar from '@/components/CommandBar';
import { Calendar, Clock, ArrowRight, CalendarDays, ListTodo, Settings } from 'lucide-react';
import { sendPrompt, CalendarResponse } from '@/lib/api';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

const Dashboard = () => {
  const [response, setResponse] = useState<CalendarResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, authLoading, navigate]);

  const handlePromptSubmit = async (prompt: string) => {
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

  if (authLoading) {
    return (
      <div className="min-h-screen w-full bg-white dark:bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-white dark:bg-black">
      <Header />
      
      <main className="pt-32 section-padding pb-20">
        <div className="max-w-7xl mx-auto animate-fade-up">
          {/* Welcome Section */}
          <div className="mb-8 text-center">
            <div className="inline-flex items-center justify-center p-2 mb-6 rounded-full bg-primary/10 text-primary">
              <Calendar className="w-5 h-5 mr-2" />
              <span className="text-sm font-medium">Your Calendar Dashboard</span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4 tracking-tight">
              Welcome back, {user?.name?.split(' ')[0] || 'User'}
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Manage your calendar with natural language commands
            </p>
          </div>

          <Tabs defaultValue="command" className="w-full">
            <TabsList className="mb-6 glass dark:bg-black/30">
              <TabsTrigger value="command" className="flex items-center gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-black">
                <Calendar className="h-4 w-4" />
                <span>Calendar Assistant</span>
              </TabsTrigger>
              <TabsTrigger value="upcoming" className="flex items-center gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-black">
                <ListTodo className="h-4 w-4" />
                <span>Upcoming Events</span>
              </TabsTrigger>
              <TabsTrigger value="settings" className="flex items-center gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-black">
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="command" className="space-y-8">
              <div className="glass p-6 text-left max-w-4xl mx-auto">
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">AI Calendar Assistant</h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  Use natural language to manage your calendar
                </p>
                <CommandBar 
                  placeholder='Try "Schedule a meeting with John at 3 PM tomorrow"'
                  onSubmit={handlePromptSubmit}
                  isLoading={isLoading}
                />
                
                {!response && !isLoading && (
                  <div className="flex flex-wrap justify-center gap-4 mt-6 text-sm text-gray-500 dark:text-gray-300">
                    <span className="glass px-3 py-1 cursor-pointer hover:bg-white/20 dark:hover:bg-black/40 transition"
                      onClick={() => handlePromptSubmit("What events do I have this week?")}>
                      "What events do I have this week?"
                    </span>
                    <span className="glass px-3 py-1 cursor-pointer hover:bg-white/20 dark:hover:bg-black/40 transition"
                      onClick={() => handlePromptSubmit("Schedule a team meeting tomorrow at 10am")}>
                      "Schedule a team meeting tomorrow at 10am"
                    </span>
                    <span className="glass px-3 py-1 cursor-pointer hover:bg-white/20 dark:hover:bg-black/40 transition"
                      onClick={() => handlePromptSubmit("Find a free time slot next week for lunch")}>
                      "Find free time for lunch next week"
                    </span>
                  </div>
                )}
              </div>

              {/* Response Display */}
              {response && (
                <div className="animate-fade-up">
                  {response.message && (
                    <div className="glass p-6 text-left max-w-4xl mx-auto">
                      <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Response</h2>
                      <p className="text-gray-800 dark:text-gray-200">{response.message}</p>
                      
                      <div className="mt-6">
                        <Button 
                          onClick={() => setResponse(null)} 
                          variant="outline"
                          className="glass hover:bg-white/20 dark:hover:bg-black/40 transition"
                        >
                          New Request
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {response.events && response.events.length > 0 && (
                    <div className="glass p-6 text-left max-w-4xl mx-auto mt-4">
                      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Events</h2>
                      <div className="space-y-4">
                        {response.events.map((event, index) => (
                          <div key={index} className="glass p-4">
                            <h3 className="font-medium text-gray-900 dark:text-white">{event.summary}</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{event.description}</p>
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
                      
                      <div className="mt-6">
                        <Button 
                          onClick={() => setResponse(null)} 
                          variant="outline"
                          className="glass hover:bg-white/20 dark:hover:bg-black/40 transition"
                        >
                          New Request
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {response.error && (
                    <div className="glass p-6 text-left max-w-4xl mx-auto bg-red-50 dark:bg-red-900/20">
                      <h2 className="text-xl font-semibold mb-2 text-red-700 dark:text-red-400">Error</h2>
                      <p className="text-red-600 dark:text-red-300">{response.error}</p>
                      
                      <div className="mt-6">
                        <Button 
                          onClick={() => setResponse(null)} 
                          variant="outline"
                          className="glass hover:bg-white/20 dark:hover:bg-black/40 transition"
                        >
                          New Request
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>

            <TabsContent value="upcoming">
              <div className="glass p-6 text-left max-w-4xl mx-auto">
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Upcoming Events</h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  View and manage your upcoming calendar events
                </p>
                
                <div className="text-center py-8">
                  <CalendarDays className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500" />
                  <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">Your upcoming events will appear here</h3>
                  <p className="mt-2 text-gray-600 dark:text-gray-300">
                    Use the Calendar Assistant tab to view your events
                  </p>
                  <Button 
                    className="mt-4 gap-2"
                    onClick={() => {
                      const commandTab = document.querySelector('[data-value="command"]') as HTMLElement;
                      if (commandTab) commandTab.click();
                      handlePromptSubmit("What events do I have this week?");
                    }}
                  >
                    View This Week's Events
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="settings">
              <div className="glass p-6 text-left max-w-4xl mx-auto">
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Account Settings</h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  Manage your account and preferences
                </p>
                
                <div className="space-y-6">
                  <div className="glass p-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Profile Information</h3>
                    <div className="flex items-center space-x-4">
                      {user?.picture ? (
                        <img 
                          src={user.picture} 
                          alt={user.name} 
                          className="h-16 w-16 rounded-full"
                        />
                      ) : (
                        <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="text-xl font-medium text-primary">
                            {user?.name?.charAt(0) || 'U'}
                          </span>
                        </div>
                      )}
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{user?.name}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-300">{user?.email}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="glass p-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Connected Accounts</h3>
                    <div className="glass p-4 border-green-200 dark:border-green-800 bg-green-50/30 dark:bg-green-900/20 flex items-center justify-between">
                      <div className="flex items-center">
                        <Calendar className="h-5 w-5 text-green-600 dark:text-green-400 mr-2" />
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">Google Calendar</p>
                          <p className="text-sm text-gray-600 dark:text-gray-300">Connected</p>
                        </div>
                      </div>
                      <Button variant="outline" size="sm" disabled className="glass">
                        Connected
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
};

export default Dashboard; 