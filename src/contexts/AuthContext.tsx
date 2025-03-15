import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'sonner';

// Define the base URL for your API - dynamically set based on environment
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isDevelopment 
  ? 'http://127.0.0.1:5000/api'  // Local development backend
  : 'https://calgentic.onrender.com/api';  // Production backend

// ... rest of the file ...
const SERVER_BASE_URL = isDevelopment
  ? 'http://127.0.0.1:5000'
  : 'https://calgentic.onrender.com'; 

interface User {
  id: string;
  name: string;
  email: string;
  picture?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper function for API calls with better error handling
const fetchWithErrorHandling = async (url: string, options: RequestInit = {}) => {
  try {
    const response = await fetch(url, options);
    return response;
  } catch (error) {
    console.error(`Fetch error for ${url}:`, error);
    // Add more detailed error information
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      console.error('This might be a CORS issue or the server is not responding');
      console.error('Check that the server is running and CORS is properly configured');
      console.error('Current API URL:', url);
    }
    throw error;
  }
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const checkAuth = async (): Promise<boolean> => {
    try {
      // Check if we're on the auth callback route
      if (window.location.pathname === '/auth/callback') {
        // Check URL parameters for auth_success
        const urlParams = new URLSearchParams(window.location.search);
        const authSuccess = urlParams.get('auth_success');
        const userEmail = urlParams.get('user');
        
        if (authSuccess === 'true' && userEmail) {
          // If we have auth_success=true in URL, we can set authenticated immediately
          setIsAuthenticated(true);
          
          // Clean up URL parameters by redirecting to home page
          window.history.replaceState({}, document.title, '/');
          
          // Still check with the server to get full user details
          const response = await fetchWithErrorHandling(`${API_BASE_URL}/check-auth`, {
            method: 'GET',
            credentials: 'include',
          });
          
          if (response.ok) {
            const data = await response.json();
            if (data.authenticated) {
              setUser(data.user);
              return true;
            }
          }
          
          return true;
        }
      }
      
      // Regular auth check
      console.log('Performing regular auth check...');
      const response = await fetchWithErrorHandling(`${API_BASE_URL}/check-auth`, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        
        if (data.authenticated) {
          setUser(data.user);
          setIsAuthenticated(true);
          console.log('Auth check successful:', data.user);
          return true;
        } else {
          setUser(null);
          setIsAuthenticated(false);
          console.log('Auth check failed:', data.user);
          return false;
        }
      } else {
        // Handle non-200 responses
        console.error('Auth check failed:', response.status);
        setUser(null);
        setIsAuthenticated(false);
        return false;
      }
    } catch (error) {
      // Handle network errors
      console.error('Auth check error:', error);
      setUser(null);
      setIsAuthenticated(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = () => {
    // This should point to the correct login endpoint on your backend
    window.location.href = `${SERVER_BASE_URL}/api/login`;
  };

  const logout = async () => {
    try {
      const response = await fetchWithErrorHandling(`${API_BASE_URL}/logout`, {
        method: 'POST',
        credentials: 'include',
      });

      if (response.ok) {
        setUser(null);
        setIsAuthenticated(false);
        toast.success('Logged out successfully');
      } else {
        toast.error('Failed to logout');
      }
    } catch (error) {
      toast.error('Network error during logout');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 