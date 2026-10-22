import { useState } from "react"
import LandingPage from "./components/LandingPage"
import RecipePage from "./components/RecipePage"
import CookingPage from "./components/CookingPage"
import { API_URL, readApiResponse } from "./api"

function App() {

  const [url, setUrl] = useState("")
  const [recipe, setRecipe] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [transcriptMode, setTranscriptMode] = useState("captions")
  const [isCooking, setIsCooking] = useState(false)

  async function generateRecipe() {

    if (!url.trim()) {
      setError("Paste a YouTube video link first.")
      return
    }

    setLoading(true)
    setError("")

    try {

      const response = await fetch(
        `${API_URL}/transcript/?url=${encodeURIComponent(url.trim())}&mode=${transcriptMode}`
      )
      const data = await readApiResponse(response, "Could not generate a recipe. Please try again.")
      if (
        typeof data.title !== "string" ||
        !Array.isArray(data.ingredients) || data.ingredients.length === 0 ||
        !Array.isArray(data.steps) || data.steps.length === 0 ||
        !Array.isArray(data.equipment) ||
        !Array.isArray(data.safety_warnings) ||
        !Array.isArray(data.first_aid)
      ) {
        throw new Error("The server returned an incomplete recipe. Please try another video.")
      }

      setRecipe(data)
      setIsCooking(false)

    } catch (err) {

      console.error(err)
      setError(err instanceof TypeError
        ? "Could not reach the backend. Start the API server and try again."
        : err.message || "An error occurred while fetching the recipe.")

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

  function tryAnotherVideo() {
    setRecipe(null)
    setIsCooking(false)
    setError("")
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
        tryAnotherVideo={tryAnotherVideo}
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
