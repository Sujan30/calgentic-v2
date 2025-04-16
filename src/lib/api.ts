import axios from 'axios';

// Define the base URL for your API
const isDevelopment = process.env.NODE_ENV === 'development';
export const API_BASE_URL = isDevelopment 
  ? 'http://127.0.0.1:5001/api'
  : 'https://calgentic.onrender.com/api';

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
    // Encode the prompt for URL safety
    const encodedPrompt = encodeURIComponent(prompt);
    const response = await fetch(getFullApiUrl(`prompt/${encodedPrompt}`), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending prompt:', error);
    if (error instanceof Error) {
      return { error: error.message };
    }
    return { error: 'Failed to process your request. Please try again.' };
  }
}

// Add other API functions here... 