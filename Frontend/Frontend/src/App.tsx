import './App.css'
import { useState } from 'react'

function App() {
  const [loading, setLoading] = useState(false);

  // Inside App.tsx
const startAnalysis = async () => {
    setLoading(true);
    try {
        const response = await fetch('http://localhost:5193/music/play');
        const data = await response.json();
        
        if (data.spotifyLink) {
            // This will navigate the current tab to the Spotify track
            window.location.href = data.spotifyLink;
        } else {
            console.error("No link found in response:", data);
            alert("Analysis finished, but no music was found.");
        }
    } catch (err) {
        console.error("Connection failed", err);
        alert("Check if your Backend is running on port 5193!");
    } finally {
        setLoading(false);
    }
}


  return (
    <div className="app-container">
      <h1> Music Recommandation based on Facial Emotion</h1>
      <p>Analyze your face, get the perfect track.</p>
      
      <button className="vibe-button" onClick={startAnalysis} disabled={loading}>
        {loading ? "Waiting for 'Q' key..." : "Open Camera"}
      </button>

      {loading && <p style={{marginTop: '20px'}}>Look at the camera window and press 'Q' when ready!</p>}
    </div>
  )
}

export default App