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

      <form className="input-section" onSubmit={(event) => { event.preventDefault(); generateRecipe(); }}>

        <input
          type="url"
          aria-label="YouTube video URL"
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

        <button type="submit" disabled={loading}>
          Generate Recipe
        </button>

      </form>

      {error && (
        <div className="error-message" role="alert">
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
