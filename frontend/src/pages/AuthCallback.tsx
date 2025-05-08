import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';

const AuthCallback = () => {
  const { isAuthenticated, checkAuth } = useAuth();
  const [isVerifying, setIsVerifying] = useState(true);
  const [verificationAttempts, setVerificationAttempts] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const verifyAuth = async () => {
      // Parse URL parameters
      const searchParams = new URLSearchParams(location.search);
      const error = searchParams.get('error');
      const code = searchParams.get('code');
      const authSuccess = searchParams.get('auth_success');
      
      console.log('AuthCallback: URL parameters', { error, code, authSuccess });
      
      // Handle error case
      if (error) {
        setIsVerifying(false);
        navigate('/login', { state: { error: 'Authentication failed. Please try again.' } });
        return;
      }

      // If we have an auth_success parameter, we can navigate directly
      if (authSuccess === 'true') {
        await checkAuth();
        setIsVerifying(false);
        navigate('/dashboard');
        return;
      }

      // If we have a code but no auth_success yet, we need to verify authentication
      if (code) {
        try {
          console.log('AuthCallback: Verifying with code');
          // Check authentication status
          await checkAuth();
          
          console.log('AuthCallback: Auth check complete, isAuthenticated:', isAuthenticated);
          
          // If authenticated, navigate to dashboard
          if (isAuthenticated) {
            setIsVerifying(false);
            navigate('/dashboard');
            return;
          }
          
          // If not authenticated yet but we still have attempts left
          if (verificationAttempts < 5) {
            console.log(`AuthCallback: Not authenticated yet, attempt ${verificationAttempts + 1} of 5`);
            // Increment attempts and try again after a delay
            setVerificationAttempts(prev => prev + 1);
            setTimeout(verifyAuth, 1000 * verificationAttempts); // Increasing delay with each attempt
          } else {
            // If we've tried enough times and still not authenticated
            console.log('AuthCallback: Authentication timed out after 5 attempts');
            setIsVerifying(false);
            navigate('/login', { state: { error: 'Authentication timed out. Please try again.' } });
          }
        } catch (error) {
          console.error('AuthCallback: Error during verification', error);
          setIsVerifying(false);
          navigate('/login', { state: { error: 'Authentication failed. Please try again.' } });
        }
      } else {
        // If no code or auth_success, redirect to login
        console.log('AuthCallback: No code or auth_success parameter');
        setIsVerifying(false);
        navigate('/login', { state: { error: 'Invalid authentication callback. Please try again.' } });
      }
    };

    verifyAuth();
  }, [checkAuth, isAuthenticated, location.search, navigate, verificationAttempts]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white dark:bg-black">
      {isVerifying ? (
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <h1 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">Verifying your authentication...</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-300">
            Please wait while we complete the login process.
          </p>
          {verificationAttempts > 0 && (
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              Attempt {verificationAttempts} of 5...
            </p>
          )}
        </div>
      ) : (
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <h1 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">Redirecting...</h1>
        </div>
      )}
    </div>
  );
};

export default AuthCallback; 