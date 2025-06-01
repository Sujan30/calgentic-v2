import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Calendar } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';
const SERVER_BASE_URL = import.meta.env.VITE_SERVER_BASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';

const Login = () => {
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get error from URL parameters
  const urlParams = new URLSearchParams(location.search);
  const error = urlParams.get('error');

  // Check if user is already authenticated
  const checkAuth = async () => {
    try {
      console.log('Login: Checking if user is already authenticated...');
      const response = await fetch(`${API_BASE_URL}/api/check-auth`, {
        method: "GET",
        credentials: "include",
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      console.log('Login: Auth check response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Login: Auth check response data:', data);
        
        if (data.authenticated) {
          console.log('Login: User already authenticated, redirecting to dashboard');
          // User is already logged in, redirect to dashboard
          navigate('/dashboard');
          return;
        } else {
          console.log('Login: User not authenticated:', data.message);
        }
      }
    } catch (error) {
      console.error("Login: Auth check error:", error);
    } finally {
      setIsCheckingAuth(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleLogin = () => {
    console.log("Initiating login with server URL:", SERVER_BASE_URL);
    window.location.href = `${SERVER_BASE_URL}/api/login`;
  };

  const getErrorMessage = (errorCode: string) => {
    switch (errorCode) {
      case 'no_code':
        return 'Authorization failed. Please try again.';
      case 'token_exchange_failed':
        return 'Authentication failed. Please try again.';
      case 'no_id_token':
        return 'Authentication incomplete. Please try again.';
      case 'exception':
        return 'An error occurred during authentication. Please try again.';
      case 'auth_timeout':
        return 'Authentication timed out. Please try signing in again.';
      default:
        return 'Authentication failed. Please try again.';
    }
  };

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-black">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">Checking authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white dark:bg-black px-4">
      <div className="w-full max-w-md space-y-8 text-center">
        <div>
          <div className="flex items-center justify-center gap-2 mb-6">
            <Calendar className="w-8 h-8 text-primary" />
            <span className="text-2xl font-bold text-gray-900 dark:text-white">CalGentic</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome to CalGentic
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            Sign in to manage your calendar with AI
          </p>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
            <p className="text-sm text-red-600 dark:text-red-400">{getErrorMessage(error)}</p>
          </div>
        )}

        <div className="space-y-4">
          <Button
            onClick={handleLogin}
            className="w-full flex items-center justify-center gap-2 py-3"
            size="lg"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </Button>
        </div>

        <div className="text-xs text-gray-500 dark:text-gray-400">
          By signing in, you agree to our Terms of Service and Privacy Policy
        </div>
      </div>
    </div>
  );
};

export default Login; 