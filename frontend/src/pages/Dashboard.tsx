import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import CommandBar from '@/components/CommandBar';
import { Calendar, Clock, ArrowRight, CalendarDays, ListTodo, Settings, LogOut, Link } from 'lucide-react';
import { sendPrompt, CalendarResponse } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import Footer from '@/components/Footer';
import { ThemeToggle } from '@/components/ThemeToggle';

// Environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';
const SERVER_BASE_URL = import.meta.env.VITE_SERVER_BASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';

interface User {
  id: string;
  name: string;
  email: string;
  picture?: string;
}

const Dashboard = () => {
  const [response, setResponse] = useState<CalendarResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Check authentication status
  const checkAuth = async (): Promise<boolean> => {
    try {
      console.log('Dashboard: Checking authentication...');
      const response = await fetch(`${API_BASE_URL}/api/check-auth`, {
        method: "GET",
        credentials: "include",
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      console.log('Dashboard: Auth check response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Dashboard: Auth check response data:', data);
        
        if (data.authenticated && data.user) {
          setUser(data.user);
          setIsAuthenticated(true);
          console.log('Dashboard: User authenticated successfully:', data.user.email);
          toast.success(`Welcome back, ${data.user.name}!`);
          return true;
        } else {
          console.log('Dashboard: User not authenticated:', data.message);
          console.log('Dashboard: Debug info:', data.debug);
          setUser(null);
          setIsAuthenticated(false);
          
          // Show a helpful message for debugging
          if (data.debug?.session_exists && !data.debug?.user_exists) {
            console.warn('Dashboard: Session exists but no user data - OAuth callback may have failed');
            toast.error('Authentication incomplete. Please try signing in again.');
          }
          return false;
        }
      } else {
        console.error("Dashboard: Auth check failed with status:", response.status);
        const errorData = await response.text();
        console.error("Dashboard: Auth check error data:", errorData);
        setUser(null);
        setIsAuthenticated(false);
        toast.error('Failed to verify authentication. Please try signing in again.');
        return false;
      }
    } catch (error) {
      console.error("Dashboard: Auth check error:", error);
      setUser(null);
      setIsAuthenticated(false);
      toast.error('Network error. Please check your connection and try again.');
      return false;
    } finally {
      setAuthLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/logout`, {
        method: "POST",
        credentials: "include",
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setUser(null);
        setIsAuthenticated(false);
        toast.success("Logged out successfully");
        navigate('/login');
      } else {
        toast.error("Failed to log out");
      }
    } catch (error) {
      toast.error("Network error during logout");
    }
  };

  // Check authentication on component mount with retry logic
  useEffect(() => {
    console.log('Dashboard: Component mounted, checking auth...');
    
    const performAuthCheck = async () => {
      const isAuth = await checkAuth();
      
      // If we're coming from OAuth redirect and not authenticated, 
      // wait a moment and try again (session might still be propagating)
      if (!isAuth && window.location.search.includes('from_oauth')) {
        console.log('Dashboard: From OAuth redirect but not authenticated, retrying in 1 second...');
        setTimeout(async () => {
          const retryAuth = await checkAuth();
          if (!retryAuth) {
            console.log('Dashboard: Retry failed, redirecting to login');
            navigate('/login?error=auth_failed');
          }
        }, 1000);
      }
    };
    
    performAuthCheck();
  }, [navigate]);

  // Redirect to login if not authenticated (with a delay to ensure auth check completes)
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      console.log('Dashboard: User not authenticated, redirecting to login in 2 seconds...');
      const timer = setTimeout(() => {
        console.log('Dashboard: Redirecting to login now');
        navigate('/login?error=not_authenticated');
      }, 2000);
      
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, authLoading, navigate]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handlePromptSubmit = async (prompt: string) => {
    if (!prompt.trim()) return;
    
    // Ensure user is authenticated before making calendar requests
    if (!isAuthenticated || !user) {
      toast.error('Please sign in to use the calendar assistant');
      navigate('/login');
      return;
    }
    
    setIsLoading(true);
    
    try {
      console.log('Dashboard: Sending prompt:', prompt);
      const result = await sendPrompt(prompt);
      console.log('Dashboard: Received result:', result);
      
      setResponse(result);
      
      if (result.error) {
        // Handle specific error types
        if (result.error.includes('authentication') || result.error.includes('token')) {
          toast.error('Authentication expired. Please sign in again.');
          setIsAuthenticated(false);
          navigate('/login?error=token_expired');
        } else if (result.error.includes('calendar') || result.error.includes('permission')) {
          toast.error('Calendar access denied. Please check your permissions.');
        } else {
          toast.error(result.error);
        }
        console.error("Dashboard: Error from server:", result.error);
      } else if (result.message) {
        toast.success("Request processed successfully!");
      } else if (result.events && result.events.length > 0) {
        toast.success(`Found ${result.events.length} event(s)`);
      }
    } catch (error) {
      console.error("Dashboard: Error processing request:", error);
      
      // Handle network and authentication errors
      if (error instanceof Error) {
        if (error.message.includes('401') || error.message.includes('authentication')) {
          toast.error('Authentication expired. Please sign in again.');
          setIsAuthenticated(false);
          navigate('/login?error=auth_expired');
        } else if (error.message.includes('403') || error.message.includes('permission')) {
          toast.error('Access denied. Please check your calendar permissions.');
        } else {
          toast.error(`Error: ${error.message}`);
        }
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
          <p className="mt-4 text-gray-600 dark:text-gray-300">Verifying your authentication...</p>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Setting up your calendar dashboard
          </p>
        </div>
      </div>
    );
  }

  // Show error if not authenticated (this shouldn't normally be visible due to redirect)
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen w-full bg-white dark:bg-black flex items-center justify-center">
        <div className="text-center max-w-md mx-auto">
          <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Calendar className="w-8 h-8 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Authentication Required
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            You need to sign in to access your calendar dashboard.
          </p>
          <Button 
            onClick={() => navigate('/login')}
            className="gap-2"
          >
            <Calendar className="w-4 h-4" />
            Sign In
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-white dark:bg-black">
      {/* Simplified Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-black border-b border-gray-200 dark:border-gray-800">
        <div className="container flex items-center justify-between h-16 px-4 mx-auto">
          <div className="flex items-center gap-2">
            <Link to="/" className="flex items-center gap-2 cursor-pointer">
              <Calendar className="w-6 h-6 text-primary" />
              <span className="text-xl font-bold text-gray-900 dark:text-white">CalGentic</span>
            </Link>
          </div>
          
          <div className="flex items-center gap-4">
            {user && (
              <div className="relative" ref={dropdownRef}>
                <button
                  className="flex items-center gap-2 focus:outline-none"
                  onClick={() => setDropdownOpen((open) => !open)}
                >
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="h-8 w-8 rounded-full"
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <span className="text-sm font-medium text-primary">
                        {user.name?.charAt(0) || "U"}
                      </span>
                    </div>
                  )}
                  <span className="text-sm text-gray-700 dark:text-gray-300">{user.name}</span>
                </button>
                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-40 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded shadow-lg z-50">
                    <button
                      onClick={logout}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-primary dark:hover:text-primary transition"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </button>
                  </div>
                )}
              </div>
            )}
            <ThemeToggle />
          </div>
        </div>
      </header>
      
      <main className="pt-32 section-padding pb-20">
        <div className="max-w-4xl mx-auto animate-fade-up">
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
            <TabsList className="mb-6 glass dark:bg-black/30 w-full">
              <TabsTrigger value="command" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <span>Calendar Assistant</span>
              </TabsTrigger>
              <TabsTrigger value="settings" className="flex items-center gap-2">
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
                      "What events do I have today?"
                    </span>
                    <span className="glass px-3 py-1 cursor-pointer hover:bg-white/20 dark:hover:bg-black/40 transition"
                      onClick={() => handlePromptSubmit("Schedule a team meeting tomorrow at 10am")}>
                      "Schedule a team meeting tomorrow at 10am"
                    </span>
                    <span className="glass px-3 py-1 cursor-pointer hover:bg-white/20 dark:hover:bg-black/40 transition"
                      onClick={() => handlePromptSubmit("Find a free time slot next week for lunch")}>
                      "Create a meeting with sujan for next monday at 10am"
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
    <Footer/>
    </div>
  );
};

export default Dashboard; 