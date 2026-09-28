import { useState } from 'react'
import './App.css'

type Track = { track_id: string; title: string; artist: string; score: number; energy: number; valence: number }
type Result = { model_version: string; recommendations: Track[] }
const api = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const moods = ['happy', 'calm', 'sad', 'energetic'] as const

function App() {
  const [mood, setMood] = useState<string>('happy')
  const [result, setResult] = useState<Result | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function recommend() {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const response = await fetch(`${api}/v1/recommendations`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mood, k: 8 }), signal: AbortSignal.timeout(10000),
      })
      if (!response.ok) throw new Error(response.status === 503
        ? 'The model is not ready. Run the training pipeline and restart the API.'
        : `Recommendation request failed (${response.status}).`)
      setResult(await response.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to reach the recommendation service.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <header><span className="brand">◉ RESONANCE</span><span className="tag">ML ENGINEERING LAB</span></header>
      <section className="intro">
        <p className="eyebrow">YOUR MOOD. A LEARNED RANKING.</p>
        <h1>Find your<br /><span>next frequency.</span></h1>
        <p>A music recommendation experiment powered by a trained preference model.
          Choose a mood to explore its ranked catalog.</p>
      </section>
      <section className="controls" aria-label="Recommendation preferences">
        <h2>How are you feeling?</h2>
        <div className="moods">{moods.map(value => <button key={value}
          className={value === mood ? 'selected' : ''} aria-pressed={value === mood}
          disabled={loading} onClick={() => { setMood(value); setResult(null) }}>{value}</button>)}</div>
        <button className="submit" disabled={loading} onClick={recommend}>
          {loading ? 'Ranking the catalog…' : 'Discover tracks ↗'}</button>
      </section>
      {error && <p className="error" role="alert">{error}</p>}
      <section aria-live="polite" aria-busy={loading}>
        {result && <>
          <div className="results-heading"><h2>Your listening shortlist</h2>
            <span>MODEL {result.model_version.slice(0, 8)}</span></div>
          <ol className="tracks">{result.recommendations.map((track, i) => <li key={track.track_id}>
            <span className="number">{String(i + 1).padStart(2, '0')}</span>
            <div className="track-name"><h3>{track.title}</h3><p>{track.artist}</p></div>
            <div className="score"><strong>{track.score.toFixed(2)}</strong><span>ranking score</span></div>
          </li>)}</ol>
        </>}
      </section>
      <footer><strong>A transparent demo.</strong> Tracks and training interactions are synthetic.
        Scores are model outputs, not measured listener satisfaction. No camera or Spotify account needed.
        <a href={`${api}/docs`} target="_blank" rel="noreferrer">Explore the API ↗</a></footer>
    </main>
  )
}

export default App
