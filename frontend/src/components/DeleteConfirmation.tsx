import React from 'react';
import { AlertTriangle, Calendar, Clock, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface Event {
  id?: string;
  summary: string;
  description?: string;
  start: string;
  end: string;
  link?: string;
}

interface DeleteConfirmationProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  events: Event[];
  isLoading?: boolean;
  confidence?: 'high' | 'medium' | 'low';
  confirmationMessage?: string;
}

const DeleteConfirmation: React.FC<DeleteConfirmationProps> = ({
  isOpen,
  onClose,
  onConfirm,
  events,
  isLoading = false,
  confidence = 'high',
  confirmationMessage
}) => {
  const getConfidenceColor = () => {
    switch (confidence) {
      case 'high': return 'text-green-600 dark:text-green-400';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400';
      case 'low': return 'text-red-600 dark:text-red-400';
    }
  };

  const getConfidenceText = () => {
    switch (confidence) {
      case 'high': return 'High confidence match';
      case 'medium': return 'Medium confidence match - please verify';
      case 'low': return 'Low confidence match - please double check';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <DialogTitle className="text-lg font-semibold">
              Delete Event{events.length > 1 ? 's' : ''}
            </DialogTitle>
          </div>
          <DialogDescription className="text-sm text-gray-600 dark:text-gray-300">
            {confirmationMessage || `You are about to delete ${events.length} event${events.length > 1 ? 's' : ''}. This action cannot be undone.`}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {/* Confidence indicator */}
          <div className={`mb-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800 border-l-4 ${
            confidence === 'high' ? 'border-green-500' : 
            confidence === 'medium' ? 'border-yellow-500' : 'border-red-500'
          }`}>
            <p className={`text-sm font-medium ${getConfidenceColor()}`}>
              {getConfidenceText()}
            </p>
          </div>

          {/* Event preview */}
          <div className="space-y-3">
            <h3 className="font-medium text-gray-900 dark:text-white">
              Event{events.length > 1 ? 's' : ''} to be deleted:
            </h3>
            
            {events.map((event, index) => (
              <div key={index} className="p-4 border border-red-200 dark:border-red-800 rounded-lg bg-red-50/30 dark:bg-red-900/20">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 dark:text-white flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      {event.summary}
                    </h4>
                    
                    {event.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        {event.description}
                      </p>
                    )}
                    
                    <div className="flex items-center mt-2 text-sm text-gray-600 dark:text-gray-300">
                      <Clock className="w-4 h-4 mr-1" />
                      <span>
                        {new Date(event.start).toLocaleString()} - {new Date(event.end).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  
                  <X className="h-4 w-4 text-red-500 mt-1" />
                </div>
              </div>
            ))}
          </div>

          {/* Warning for low confidence */}
          {confidence === 'low' && (
            <div className="mt-4 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                ⚠️ The system has low confidence in this match. Please verify these are the correct events before deleting.
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={isLoading}
            className="gap-2"
          >
            {isLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
            Delete Event{events.length > 1 ? 's' : ''}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DeleteConfirmation;