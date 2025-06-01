import React from 'react';
import { Calendar, Info } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const Header = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-black border-b border-gray-200 dark:border-gray-800">
      <div className="container flex items-center justify-between h-16 px-4 mx-auto">
        <div className="flex items-center gap-2">
          <Link to="/" className="flex items-center gap-2">
            <Calendar className="w-6 h-6 text-primary" />
            <span className="text-xl font-bold text-gray-900 dark:text-white">CalGentic</span>
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/about">
            <Button variant="ghost" size="sm" className="gap-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white">
              <Info className="h-4 w-4" />
              <span>About</span>
            </Button>
          </Link>
          
          <Link to="/login">
            <Button variant="default" size="sm" className="gap-2">
              <Calendar className="h-4 w-4" />
              <span>Sign In</span>
            </Button>
          </Link>
          
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
};

export default Header;
