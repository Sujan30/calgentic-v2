import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'sonner';

// Load environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://calgentic.onrender.com/api";
const SERVER_BASE_URL = import.meta.env.VITE_SERVER_BASE_URL || "https://calgentic.onrender.com";
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "543793899909-bmpj50nlv128esp3ca44eaan2vlm8g82.apps.googleusercontent.com";
const FRONTEND_REDIRECT_URI = import.meta.env.VITE_FRONTEND_REDIRECT_URI || "https://calgentic.onrender.com/auth/callback";

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
      const urlParams = new URLSearchParams(window.location.search);
      const authSuccess = urlParams.get('auth_success');
      const userEmail = urlParams.get('user');
      const code = urlParams.get("code");

      if (authSuccess === 'true' && userEmail) {
        setIsAuthenticated(true);
      }

      if (code) {
        console.log("OAuth code detected, sending to backend...");
        const response = await fetch(`${SERVER_BASE_URL}/auth/callback?code=${code}`, {
          method: "GET",
          credentials: "include",
        });

        if (response.ok) {
          console.log("OAuth code successfully processed");
          window.history.replaceState({}, document.title, window.location.pathname);
        } else {
          console.error("Failed to process OAuth code:", response.status);
        }
      }

      const response = await fetch(`${API_BASE_URL}/check-auth`, {
        method: "GET",
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        if (data.authenticated) {
          setUser(data.user);
          setIsAuthenticated(true);
          return true;
        } else {
          setUser(null);
          setIsAuthenticated(false);
          return false;
        }
      } else {
        console.error("Auth check failed:", response.status);
        setUser(null);
        setIsAuthenticated(false);
        return false;
      }
    } catch (error) {
      console.error("Auth check error:", error);
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

  // Google OAuth login function
  const login = () => {
    const SCOPES = [
      "openid",
      "https://www.googleapis.com/auth/calendar",
      "https://www.googleapis.com/auth/userinfo.email",
      "https://www.googleapis.com/auth/userinfo.profile",
    ];

    const googleLoginUrl = `https://accounts.google.com/o/oauth2/auth?client_id=${GOOGLE_CLIENT_ID}&redirect_uri=${encodeURIComponent(FRONTEND_REDIRECT_URI)}&response_type=code&scope=${encodeURIComponent(SCOPES.join(" "))}&access_type=offline&prompt=consent&include_granted_scopes=true`;

    console.log("Redirecting to Google OAuth:", googleLoginUrl);
    window.location.href = googleLoginUrl;
  };

  // Logout function
  const logout = async () => {
    try {
      const response = await fetch(`${SERVER_BASE_URL}/auth/logout`, {
        method: "GET", // Your backend uses GET for logout
        credentials: "include",
      });

      if (response.ok) {
        setUser(null);
        setIsAuthenticated(false);
        toast.success("Logged out successfully");
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