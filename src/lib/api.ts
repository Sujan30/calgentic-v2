import axios from 'axios';

// Define the base URL for your API
export const API_BASE_URL = 'http://127.0.0.1:5000/api';

// Define response types
export interface CalendarResponse {
  message?: string;
  success?: boolean;
  error?: string;
  events?: Array<{
    summary: string;
    description: string;
    start: string;
    end: string;
    link: string;
  }>;
}

// Add this function to help with debugging
export function getFullApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
  return `${API_BASE_URL}/${cleanEndpoint}`;
}

// Function to send a prompt to the backend
export async function sendPrompt(prompt: string): Promise<CalendarResponse> {
  try {
    const response = await fetch(getFullApiUrl('prompt'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending prompt:', error);
    return { error: 'Failed to process your request. Please try again.' };
  }
}

// Add other API functions here... 