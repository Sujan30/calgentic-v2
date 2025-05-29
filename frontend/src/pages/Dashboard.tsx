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

  // Define a key that changes when the user is authenticated and available
  // This will force `CommandBar` to re-mount and reset its internal state.
  const commandBarKey = isAuthenticated && user ? user.id : 'unauthenticated';

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
                {/* Add the key prop here */}
                <CommandBar 
                  key={commandBarKey} // <-- ADD THIS LINE
                  placeholder='Try "Schedule a meeting with John at 3 PM tomorrow"'
                  onSubmit={handlePromptSubmit}
                  isLoading={isLoading}
                />
                
                {/* ... rest of your CommandBar related rendering ... */}
              </div>

              {/* ... rest of your Dashboard component ... */}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;