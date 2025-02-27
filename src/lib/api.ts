import axios from 'axios';

// Define the base URL for your API
const API_BASE_URL = 'http://127.0.0.1:5000';

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

// Function to send a prompt to the backend
export const sendPrompt = async (prompt: string): Promise<CalendarResponse> => {
  try {
    const encodedPrompt = encodeURIComponent(prompt);
    const response = await axios.get(`${API_BASE_URL}/prompt/${encodedPrompt}`, {
      timeout: 30000 // 30 seconds timeout
    });
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      // Handle Axios errors
      const errorMessage = error.response?.data?.error || error.message;
      return { 
        error: `Error: ${errorMessage}`,
        success: false
      };
    }
    // Handle other errors
    return { 
      error: 'An unexpected error occurred',
      success: false
    };
  }
}; 