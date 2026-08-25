function LandingPage({
  url,
  setUrl,
  transcriptMode,
  setTranscriptMode,
  generateRecipe,
  loading,
  error
}) {
  return (
    <div className="app">

      <h1>VoiceRecipe</h1>

      <div className="input-section">

        <input
          type="text"
          placeholder="Paste YouTube recipe URL"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
        />

        <select
          value={transcriptMode}
          onChange={(event) =>
            setTranscriptMode(event.target.value)
          }
        >

          <option value="captions">
            YouTube Captions
          </option>

          <option value="whisper" disabled>
            Whisper AI (Coming Soon)
          </option>

        </select>

        <button onClick={generateRecipe} disabled={loading}>
          Generate Recipe
        </button>

      </div>

      {error && (
        <div className="error-message" style={{color: 'red', marginTop: '1rem'}}>
          {error}
        </div>
      )}

      {loading && (
        <p>Generating recipe...</p>
      )}

    </div>
  )
}

export default LandingPage