import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'sonner';

// Load environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const SERVER_BASE_URL = import.meta.env.VITE_SERVER_BASE_URL;
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID; // Still good to have for clarity, though not directly used in frontend login initiation
const FRONTEND_REDIRECT_URI = import.meta.env.VITE_FRONTEND_REDIRECT_URI; // Still good to have for clarity

console.log("API_BASE_URL:", API_BASE_URL);
console.log("SERVER_BASE_URL:", SERVER_BASE_URL);
console.log("FRONTEND_REDIRECT_URI:", FRONTEND_REDIRECT_URI);

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

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Function to check authentication
  const checkAuth = async (): Promise<boolean> => {
    try {
      // **Removed:** No longer checking for 'auth_success' or 'user' in URL params.
      // The backend will set a session cookie, and this fetch will verify it.

      // Check session status
      const response = await fetch(`${API_BASE_URL}/api/check-auth`, {
        method: "GET",
        credentials: "include", // Crucial for sending cookies with the request
      });

      if (response.ok) {
        const data = await response.json();
        if (data.authenticated) {
          setUser(data.user); // Assume data.user contains id, name, email, and optionally picture
          setIsAuthenticated(true);
          // If we're not on the dashboard, redirect there after successful auth check
          if (!window.location.pathname.includes('/dashboard')) {
            window.location.href = '/dashboard';
          }
          return true;
        } else {
          setUser(null);
          setIsAuthenticated(false);
          // If not authenticated and on dashboard, redirect to home/login
          if (window.location.pathname.includes('/dashboard')) {
            window.location.href = '/'; // Or your login page path
          }
          return false;
        }
      } else {
        console.error("Auth check failed:", response.status);
        setUser(null);
        setIsAuthenticated(false);
        // If auth check failed and on dashboard, redirect to home/login
        if (window.location.pathname.includes('/dashboard')) {
          window.location.href = '/'; // Or your login page path
        }
        return false;
      }
    } catch (error) {
      console.error("Auth check error:", error);
      setUser(null);
      setIsAuthenticated(false);
      // If auth check error and on dashboard, redirect to home/login
      if (window.location.pathname.includes('/dashboard')) {
        window.location.href = '/'; // Or your login page path
      }
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Call checkAuth on component mount
    checkAuth();
  }, []); // Empty dependency array means this runs once on mount

  // Google OAuth login function
  const login = () => {
    // We still redirect to the backend's login endpoint.
    // The difference is what the backend does AFTER Google authenticates.
    window.location.href = `${SERVER_BASE_URL}/api/login`;
  };

  // Logout function remains the same
  const logout = async () => {
    try {
      const response = await fetch(`${SERVER_BASE_URL}/auth/logout`, {
        method: "GET",
        credentials: "include",
      });

      if (response.ok) {
        setUser(null);
        setIsAuthenticated(false);
        toast.success("Logged out successfully");
        // Redirect to home/login page after logout
        window.location.href = '/'; // Or your login page path
      } else {
        toast.error("Failed to log out");
      }
    } catch (error) {
      toast.error("Network error during logout");
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};