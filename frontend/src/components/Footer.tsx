import React from 'react';
import { Link } from 'react-router-dom';
import { Mail, Info, FileText, BookOpen } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="w-full bg-white dark:bg-black py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between space-y-6 md:space-y-0">
          
          {/* Logo or Project Name */}
          <div className="flex items-center space-x-2">
            <BookOpen className="w-6 h-6 text-primary" />
            <span className="text-lg font-semibold text-gray-900 dark:text-white">
              Calgentic
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-wrap items-center justify-center gap-6">
            <Link
              to="/about"
              className="flex items-center space-x-1 text-gray-900 dark:text-white hover:text-primary transition"
            >
              <Info className="w-5 h-5" />
              <span>About</span>
            </Link>

            <Link
              to="/tos"
              className="flex items-center space-x-1 text-gray-900 dark:text-white hover:text-primary transition"
            >
              <FileText className="w-5 h-5" />
              <span>Terms of Service</span>
            </Link>


            <a
              href="mailto:nandikolsujan@gmail.com"
              className="flex items-center space-x-1 text-gray-900 dark:text-white hover:text-primary transition"
            >
              <Mail className="w-5 h-5" />
              <span>Contact</span>
            </a>
          </nav>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-200 dark:border-gray-800 my-6"></div>

        {/* Copyright */}
        <div className="text-center">
          <p className="text-sm text-gray-900 dark:text-white">
            &copy; {new Date().getFullYear()} Calgentic. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;