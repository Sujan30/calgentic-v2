import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner'; // Assuming you use sonner for toasts

const AuthCallback = () => {
  const { isAuthenticated, checkAuth, isLoading: authContextLoading } = useAuth();
  const [isVerifying, setIsVerifying] = useState(true);
  const [verificationAttempts, setVerificationAttempts] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleAuthRedirect = async () => {
      // Parse URL parameters for potential errors from the backend
      const searchParams = new URLSearchParams(location.search);
      const authError = searchParams.get('auth_error'); // This is what your backend sends now

      if (authError) {
        setIsVerifying(false);
        // Display a user-friendly error message
        let errorMessage = 'Authentication failed. Please try again.';
        if (authError === 'no_code') {
          errorMessage = 'Authentication was interrupted. Please try again.';
        } else if (authError === 'token_exchange_failed') {
          errorMessage = 'Failed to secure your session. Please try again.';
        } else if (authError === 'no_id_token') {
          errorMessage = 'Could not retrieve user information. Please try again.';
        }
        toast.error(errorMessage);
        navigate('/login', { replace: true }); // Redirect to login, replacing history
        return;
      }

      // If no error, we proceed to check the authentication status
      // This will rely on the session cookie set by the backend
      const authenticated = await checkAuth();
      
      if (authenticated) {
        toast.success("Successfully logged in!");
        navigate('/dashboard', { replace: true }); // Redirect to dashboard, replacing history
      } else {
        // This might happen if the session wasn't properly set, or checkAuth failed
        toast.error("Failed to authenticate. Please log in again.");
        navigate('/login', { replace: true }); // Redirect to login, replacing history
      }

      setIsVerifying(false);
    };

    // Trigger the authentication handling when the component mounts or URL changes
    handleAuthRedirect();
  }, [checkAuth, navigate, location.search]); // Depend on checkAuth, navigate, and location.search

  // We can simplify the loading state as checkAuth handles its own loading.
  // The local `isVerifying` state primarily indicates if the AuthCallback's logic has completed.

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white dark:bg-black">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
        <h1 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">
          {isVerifying ? "Finalizing your login..." : "Redirecting..."}
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-300">
          Please wait while we secure your session.
        </p>
      </div>
    </div>
  );
};

export default AuthCallback;