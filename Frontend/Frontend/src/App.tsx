import './App.css'
import { useState } from 'react'

function App() {
  const [loading, setLoading] = useState(false);

  const startAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5193/music/play');
      const data = await response.json();
      
      if (data.spotifyLink) {
        window.open(data.spotifyLink, '_blank');
      }
    } catch (err) {
      console.error("Connection failed", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-container">
      <h1>Mood-to-Music AI</h1>
      <p>Analyze your face, get the perfect track.</p>
      
      <button className="vibe-button" onClick={startAnalysis} disabled={loading}>
        {loading ? "Waiting for 'Q' key..." : "Open Camera"}
      </button>

      {loading && <p style={{marginTop: '20px'}}>Look at the camera window and press 'Q' when ready!</p>}
    </div>
  )
}

export default App