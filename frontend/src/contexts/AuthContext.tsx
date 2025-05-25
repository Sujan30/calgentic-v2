import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'sonner';

// Load environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const SERVER_BASE_URL = import.meta.env.VITE_SERVER_BASE_URL;
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const FRONTEND_REDIRECT_URI = import.meta.env.VITE_FRONTEND_REDIRECT_URI;

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
      const code = urlParams.get('code'); // <-- NEW: Get the 'code' parameter

      // --- NEW LOGIC: Handle Google OAuth Callback with 'code' ---
      if (code) {
        console.log("Frontend received OAuth code. Sending to backend for token exchange...");
        setIsLoading(true); // Show loading state while processing

        try {
          const response = await fetch(`${SERVER_BASE_URL}/auth/callback`, { // <-- Adjust this backend endpoint if needed
            method: "POST", // Use POST for security and sending data in body
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              code,
              redirect_uri: FRONTEND_REDIRECT_URI, // Send the redirect_uri that was used
            }),
            credentials: "include", // Important for sending cookies (e.g., session ID)
          });

          if (response.ok) {
            const data = await response.json();
            if (data.authenticated) {
              setUser(data.user);
              setIsAuthenticated(true);
              toast.success("Logged in successfully!");
            } else {
              toast.error("Authentication failed after backend processing.");
              setUser(null);
              setIsAuthenticated(false);
            }
          } else {
            const errorText = await response.text();
            console.error("Backend token exchange failed:", response.status, errorText);
            toast.error(`Login failed: ${errorText || 'Server error'}`);
            setUser(null);
            setIsAuthenticated(false);
          }
        } catch (error) {
          console.error("Network error during backend token exchange:", error);
          toast.error("Network error during login.");
          setUser(null);
          setIsAuthenticated(false);
        } finally {
          // Clear the URL parameters but maintain the path
          // This is done whether successful or not to prevent re-processing the code
          window.history.replaceState({}, document.title, window.location.pathname);
          setIsLoading(false);
        }
        return isAuthenticated; // Return current status, might need a re-check if user was set
      }
      // --- END NEW LOGIC ---

      // Your existing logic for handling backend redirects with auth_success parameters
      // This is for if your backend *redirects back to the frontend* with a status
      if (authSuccess === 'true' && userEmail) {
        const basicUser = {
          id: userEmail,
          name: userEmail.split('@')[0],
          email: userEmail
        };
        setUser(basicUser);
        setIsAuthenticated(true);
        window.history.replaceState({}, document.title, window.location.pathname);
        return true;
      }

      // Only make the API call to check session if no specific OAuth parameters were found
      const response = await fetch(`${API_BASE_URL}/api/check-auth`, {
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
    // Call checkAuth on component mount
    checkAuth();
  }, []); // Empty dependency array means this runs once on mount

  // Google OAuth login function
  const login = () => {
    const SCOPES = [
      "openid",
      "https://www.googleapis.com/auth/calendar", // Consider if you need full calendar access or just .readonly or .events
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
        method: "GET",
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