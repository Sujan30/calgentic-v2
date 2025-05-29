import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const AuthCallback = () => {
  const { isAuthenticated, checkAuth } = useAuth();
  const [isVerifying, setIsVerifying] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleAuthRedirect = async () => {
      try {
        // Parse URL parameters
        const searchParams = new URLSearchParams(location.search);
        const error = searchParams.get('error');
        const code = searchParams.get('code');
        const authSuccess = searchParams.get('auth_success');
        const userEmail = searchParams.get('user');
        
        console.log('AuthCallback: URL parameters', { error, code, authSuccess, userEmail });
        
        // Handle error case
        if (error) {
          console.error('Authentication error:', error);
          toast.error('Authentication failed. Please try again.');
          navigate('/login');
          return;
        }

        // If we have an auth_success parameter, we can navigate directly
        if (authSuccess === 'true' && userEmail) {
          console.log('Authentication successful, redirecting to dashboard');
          await checkAuth();
          navigate('/dashboard', { replace: true });
          return;
        }

        // If we have a code, verify authentication
        if (code) {
          console.log('Verifying authentication with code');
          const isAuthenticated = await checkAuth();
          if (isAuthenticated) {
            console.log('Authentication verified, redirecting to dashboard');
            navigate('/dashboard', { replace: true });
          } else {
            console.error('Authentication verification failed');
            toast.error('Authentication failed. Please try again.');
            navigate('/login');
          }
          return;
        }

        // If we reach here, something went wrong
        console.error('No authentication parameters found');
        toast.error('Authentication failed. Please try again.');
        navigate('/login');
      } catch (error) {
        console.error('Error in auth callback:', error);
        toast.error('An error occurred during authentication. Please try again.');
        navigate('/login');
      } finally {
        setIsVerifying(false);
      }
    };

    handleAuthRedirect();
  }, [location, navigate, checkAuth]);

  if (isVerifying) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-lg">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  return null;
};

export default AuthCallback; 