import { useState } from "react"
import LandingPage from "./components/LandingPage"
import RecipePage from "./components/RecipePage"
import CookingPage from "./components/CookingPage"

function App() {

  const [url, setUrl] = useState("")
  const [recipe, setRecipe] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [transcriptMode, setTranscriptMode] = useState("captions")
  const [isCooking, setIsCooking] = useState(false)

  async function generateRecipe() {

    if (!url) return

    setLoading(true)
    setError("")

    try {

      const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(
        `${API_URL}/transcript/?url=${encodeURIComponent(url)}&mode=${transcriptMode}`
      )
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || "Failed to generate recipe")
      }

      setRecipe(data)
      setIsCooking(false)

    } catch (err) {

      console.error(err)
      setError(err.message || "An error occurred while fetching the recipe.")

    } finally {
      setLoading(false)
    }

  }

  function startCooking() {
    setIsCooking(true)
  }

  function exitCookingMode() {
    setIsCooking(false)
  }

  return (
  <>
    {!recipe && (
      <LandingPage
        url={url}
        setUrl={setUrl}
        transcriptMode={transcriptMode}
        setTranscriptMode={setTranscriptMode}
        generateRecipe={generateRecipe}
        loading={loading}
        error={error}
      />
    )}

    {recipe && !isCooking && (
      <RecipePage
        recipe={recipe}
        startCooking={startCooking}
      />
    )}

    {recipe && isCooking && (
      <CookingPage
        recipe={recipe}
        exitCookingMode={exitCookingMode}
      />
    )}
  </>
)
}

export default App