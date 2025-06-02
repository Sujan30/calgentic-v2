import React from 'react';
import Header from '@/components/Header';
import { Calendar, Github, Mail, Linkedin, ExternalLink, Code, Coffee, Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import Footer from '@/components/Footer';

const AboutSection = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div className="mb-12">
    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{title}</h2>
    <div className="space-y-4">{children}</div>
  </div>
);

const FeatureCard = ({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) => (
  <div className="glass p-6 rounded-xl">
    <div className="flex items-start">
      <div className="mr-4 p-2 bg-primary/10 text-primary rounded-lg">
        {icon}
      </div>
      <div>
        <h3 className="font-medium text-gray-900 dark:text-white mb-2">{title}</h3>
        <p className="text-gray-600 dark:text-gray-300">{description}</p>
      </div>
    </div>
  </div>
);

const About = () => {
  return (
    <div className="min-h-screen w-full bg-white dark:bg-black">
      <Header />
      
      <main className="pt-32 pb-20 px-4 md:px-6">
        <div className="max-w-4xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-16 animate-fade-up">
            <div className="inline-flex items-center justify-center p-2 mb-8 rounded-full bg-primary/10 text-primary">
              <Calendar className="w-5 h-5 mr-2" />
              <span className="text-sm font-medium">About CalGentic</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white mb-6 tracking-tight">
              AI-Powered Calendar Management
            </h1>
            
            <p className="text-lg text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
              CalGentic is a modern calendar assistant that uses artificial intelligence to simplify scheduling and event management.
            </p>
            
            <div className="flex flex-wrap justify-center gap-4">
              <a href="https://github.com/sujan30/calgentic" target="_blank" rel="noopener noreferrer">
                <Button className="gap-2">
                  <Github className="w-4 h-4" />
                  <span>View on GitHub</span>
                </Button>
              </a>
              <Link to="/">
                <Button variant="outline" className="gap-2">
                  <ExternalLink className="w-4 h-4" />
                  <span>Try the Demo</span>
                </Button>
              </Link>
            </div>
          </div>
          
          {/* About the Project */}
          <AboutSection title="About the Project">
            <p className="text-gray-600 dark:text-gray-300">
              Calgentic was created to solve the everyday challenges of calendar management. 
              I realized how tedious it was to manage my own calendar, and how much work it was to just create one event. 
              I wished for something like a text box, where I can just spit out even details, and it just adds it. 
            </p>
            <p className="text-gray-600 dark:text-gray-300">
              The project combines a React frontend with a Flask backend, integrating with Google Calendar API to provide 
              a seamless scheduling experience. The dark mode support ensures comfortable use in any lighting condition.
            </p>
          </AboutSection>
          
          {/* Key Features */}
          <AboutSection title="Key Features">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FeatureCard 
                icon={<Code className="w-5 h-5" />}
                title="Natural Language Processing"
                description="Create events by typing requests in plain English, like 'Schedule a meeting with John tomorrow at 3 PM'"
              />
              <FeatureCard 
                icon={<Calendar className="w-5 h-5" />}
                title="Google Calendar Integration"
                description="Seamlessly connects with your Google Calendar to manage all your events in one place"
              />
              <FeatureCard 
                icon={<Coffee className="w-5 h-5" />}
                title="User-Friendly Interface"
                description="Clean, intuitive design with dark mode support for comfortable use day and night"
              />
              <FeatureCard 
                icon={<Heart className="w-5 h-5" />}
                title="Open Source"
                description="Built with love and available as an open-source project for the community to use and improve"
              />
            </div>
          </AboutSection>
          
          {/* About the Developer */}
          <AboutSection title="About the Developer">
            <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
              <div className="w-32 h-32 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-800 flex-shrink-0">
                {/* Replace with your photo if desired */}
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <span className="text-4xl">👨‍💻</span>
                </div>
              </div>
              
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Sujan Nandikol Sunilkumar</h3>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  I'm a first year student at the San Jose State University studying Computer Science & Linguistics with a passion focusing on creating intuitive, AI-powered applications that solve real-world problems.
                  CalGentic represents my interest in combining natural language processing with practical utility to solve tedious tasks.
                </p>
                
                <div className="flex flex-wrap gap-3">
                  <a href="https://github.com/sujan30" target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" size="sm" className="gap-2">
                      <Github className="w-4 h-4" />
                      <span>GitHub</span>
                    </Button>
                  </a>
                  <a href="https://www.linkedin.com/in/sujan-nandikol-sunilkumar-94469b162/" target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" size="sm" className="gap-2">
                      <Linkedin className="w-4 h-4" />
                      <span>LinkedIn</span>
                    </Button>
                  </a>
                  <a href="mailto:sujan.nandikolsunilkumar@sjsu.edu">
                    <Button variant="outline" size="sm" className="gap-2">
                      <Mail className="w-4 h-4" />
                      <span>Contact</span>
                    </Button>
                  </a>
                </div>
              </div>
            </div>
          </AboutSection>
          
          {/* Technologies Used */}
          <AboutSection title="Technologies Used">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {['React', 'TypeScript', 'Flask', 'Python', 'Google Calendar API', 'Tailwind CSS', 'OpenAI', 'OAuth 2.0'].map((tech) => (
                <div key={tech} className="glass px-4 py-3 rounded-lg text-center">
                  <span className="text-gray-800 dark:text-gray-200">{tech}</span>
                </div>
              ))}
            </div>
          </AboutSection>
        </div>
      </main>
      
      {/* Footer */}

      <Footer/>
    </div>
  );
};

export default About; 