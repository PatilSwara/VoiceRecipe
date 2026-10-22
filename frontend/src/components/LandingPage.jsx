function LandingPage({
  url,
  setUrl,
  manualTranscript,
  setManualTranscript,
  transcriptMode,
  setTranscriptMode,
  generateRecipe,
  generateFromTranscript,
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
            Automatic Recipe
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

      <details className="transcript-fallback">
        <summary>Have a transcript? Paste it instead</summary>
        <p>Open the video's transcript on YouTube, copy its caption text, and paste it here. This works when the server cannot fetch captions automatically.</p>
        <label htmlFor="manual-transcript">Video transcript</label>
        <textarea
          id="manual-transcript"
          rows="8"
          value={manualTranscript}
          onChange={(event) => setManualTranscript(event.target.value)}
          placeholder="Paste the spoken recipe instructions here"
        />
        <button type="button" onClick={generateFromTranscript} disabled={loading}>
          Generate from Transcript
        </button>
      </details>

      {loading && (
        <p>Generating recipe...</p>
      )}

    </div>
  )
}

export default LandingPage
