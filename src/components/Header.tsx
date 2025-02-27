
import React from 'react';
import { Button } from "@/components/ui/button";

const Header = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass">
      <div className="container mx-auto flex items-center justify-between h-16 px-4">
        <div className="text-xl font-semibold text-gray-800">
          flowcalender
        </div>
        <div className="flex items-center gap-4">
          <Button variant="ghost">Login</Button>
          <Button className="bg-primary hover:bg-primary/90">Get Started</Button>
        </div>
      </div>
    </header>
  );
};

export default Header;
