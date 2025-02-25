import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const[prompt, setPrompt] = useState("")

  const handleSubmit = (event)=>{
    event.presentDefault()
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
          />
          <br/>
          


        </form>

      </div>
    </>
  )
}

export default App
