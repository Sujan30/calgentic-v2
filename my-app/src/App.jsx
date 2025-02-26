import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import axios from "axios"

function App() {
  const [prompt, setPrompt] = useState("")
  const [response, setResponse] = useState(null)
  const [summary, setSummary] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchResponse = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      // Add a timeout to the axios request (30 seconds)
      const encodedPrompt = encodeURIComponent(prompt)
      const res = await axios.get(`http://127.0.0.1:5000/prompt/${encodedPrompt}`, {
        timeout: 30000 // 30 seconds timeout
      })
      
      console.log(`API data received:`, res.data)
      setResponse(res.data)
      
      if (res.data.message) {
        setSummary(res.data.message)
      }
    } catch (err) {
      console.error("Error fetching data:", err)
      setError(err.message || "An error occurred while processing your request")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault()  // Corrected from presentDefault()
    console.log(`prompt: ${prompt}`)
    fetchResponse()
  }

  return (
    <>
      <div>
        <h2>Calgentic - AI Agent for your Calendar</h2>
        <br/>
        <br/>
        <form onSubmit={handleSubmit}>
          <input 
            type='text' 
            id='prompt'
            style={{width: "600px", height: "40px"}}
            name='question'
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isLoading}
          />
          <br/>
          <br/>
          <button type='submit' disabled={isLoading || !prompt.trim()}>
            {isLoading ? 'Processing...' : 'Submit'}
          </button>
          <br/>
          <br/>
          
          {isLoading && (
            <div className="loading-spinner">
              <div className="spinner"></div>
              <p>Creating your calendar event...</p>
            </div>
          )}
          
          {error && (
            <div className="error-message">
              <p>Error: {error}</p>
            </div>
          )}
          
          {response && !isLoading && !error && (
            <div className="response">
              <h2>Summary</h2>
              <p>{response.message}</p>
            </div>
          )}
        </form>
      </div>
    </>
  )
}

export default App
