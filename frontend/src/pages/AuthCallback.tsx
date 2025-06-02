import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [isVerifying, setIsVerifying] = useState(true);
  const [attempts, setAttempts] = useState(0);

  const checkAuthStatus = async () => {
    try {
      console.log(`AuthCallback: Checking authentication status (attempt ${attempts + 1})`);
      
      const response = await fetch(`${API_BASE_URL}/api/check-auth`, {
        method: "GET",
        credentials: "include",
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      console.log('AuthCallback: Auth check response status:', response.status);

      if (response.ok) {
        // Status 200 indicates successful authentication; redirect to dashboard
        console.log('AuthCallback: Authentication successful (status OK), redirecting to dashboard');
        setIsVerifying(false);
        navigate('/dashboard', { replace: true });
        return true;
      } else {
        console.error('AuthCallback: Auth check failed with status:', response.status);
        return false;
      }
    } catch (error) {
      console.error('AuthCallback: Error checking auth status:', error);
      return false;
    }
  };

  useEffect(() => {
    console.log('AuthCallback: Component mounted, waiting for authentication...');
    
    const verifyAuth = async () => {
      // Wait a bit for the backend to process the authentication
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const isAuthenticated = await checkAuthStatus();
      
      if (!isAuthenticated) {
        if (attempts < 5) {
          console.log(`AuthCallback: Not authenticated yet, retrying in 2 seconds (attempt ${attempts + 1}/5)`);
          setAttempts(prev => prev + 1);
          setTimeout(verifyAuth, 2000);
        } else {
          console.log('AuthCallback: Max attempts reached, redirecting to login');
          setIsVerifying(false);
          navigate('/login?error=auth_timeout', { replace: true });
        }
      }
    };

    verifyAuth();
  }, [navigate]);

  if (isVerifying) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-lg">Completing authentication...</p>
          <p className="text-sm text-gray-500 mt-2">
            {attempts > 0 ? `Verifying... (${attempts}/5)` : 'Please wait...'}
          </p>
        </div>
      </div>
    );
  }

  return null;
};

export default AuthCallback; 