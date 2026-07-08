import { useState } from "react"
import LandingPage from "./components/LandingPage"
import RecipePage from "./components/RecipePage"
import CookingPage from "./components/CookingPage"
import { useRef } from "react"
function App() {

  const [url, setUrl] = useState("")
  const [recipe, setRecipe] = useState(null)
  const [loading, setLoading] = useState(false)
  const [transcriptMode, setTranscriptMode] = useState("captions")
  const [isCooking, setIsCooking] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const recognitionRef = useRef(null)
  const currentStepRef = useRef(0)
  const [lastHeard, setLastHeard] = useState("")
  const [assistantReply, setAssistantReply] = useState("")

  async function generateRecipe() {

    if (!url) return

    setLoading(true)

    try {

      const response = await fetch(
      `http://127.0.0.1:8000/transcript/?url=${encodeURIComponent(url)}&mode=${transcriptMode}`
      )

      const data = await response.json()
      setRecipe(data)
      setLastHeard("")
setAssistantReply("")
      setCurrentStep(0)
      currentStepRef.current = 0
      setIsCooking(false)

    } catch (error) {

      console.error(error)

    }

    setLoading(false)
  }

function nextStep() {

  const current =
    currentStepRef.current

  if (
    current <
    recipe.steps.length - 1
  ) {

    const next = current + 1

    currentStepRef.current = next

    setCurrentStep(next)

    speakStep(
      recipe.steps[next].instruction
    )
  }
}
function previousStep() {

  const current =
    currentStepRef.current

  if (current > 0) {

    const previous = current - 1

    currentStepRef.current =
      previous

    setCurrentStep(previous)

    speakStep(
      recipe.steps[previous].instruction
    )
  }
}

async function askCookingQuestion(
  question
) {
  const response = await fetch(
    "http://127.0.0.1:8000/ask/",
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        recipe: recipe,
        current_step: currentStepRef.current,
        question: question
      })
    }
  )

  const data = await response.json()
  setAssistantReply(data.answer)
  speakStep(data.answer)
}
  function startCooking() {

  setIsCooking(true)

  setCurrentStep(0)

  currentStepRef.current = 0

  speakStep(
    recipe.steps[0].instruction
  )
}

  function exitCookingMode() {
    setIsCooking(false)
  }

  function speakStep(text) {

  window.speechSynthesis.cancel()

  const speech =
    new SpeechSynthesisUtterance(text)

  const voices =
    window.speechSynthesis.getVoices()

  const selectedVoice =
    voices.find(
      voice =>
        voice.lang === "en-US"
    )

  speech.voice = selectedVoice

  speech.lang = "en-US"

  speech.rate = 0.9

  window.speechSynthesis.speak(speech)
}
    function startVoiceCommands() {

    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition

    if (!SpeechRecognition) {

      alert("Speech recognition not supported in this browser.")

      return
    }

    const recognition = new SpeechRecognition()

    recognitionRef.current = recognition

    recognition.continuous = true

    recognition.onresult = (event) => {

      const transcript =
        event.results[event.results.length - 1][0].transcript
          .toLowerCase()
      
      setLastHeard(transcript)

      if (transcript.includes("next")) {
        nextStep()
        setAssistantReply("")
      }

      else if (
        transcript.includes("previous")
      ) {
        previousStep()
        setAssistantReply("")
      }

      else if (
        transcript.includes("repeat")
      )   {
        speakStep(
          recipe.steps[currentStepRef.current].instruction
        )
        setAssistantReply("")
      }

      else if (
        transcript.includes("exit")
      )   {
        exitCookingMode()
        setAssistantReply("")
      }
      else {

        askCookingQuestion(transcript)
      }
    }
    
    recognition.onend = () => {

      if (isCooking) {
        recognition.start()
      }
    }
  recognition.start()
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
        currentStep={currentStep}
        previousStep={previousStep}
        nextStep={nextStep}
        speakStep={speakStep}
        startVoiceCommands={startVoiceCommands}
        exitCookingMode={exitCookingMode}
        lastHeard={lastHeard}
        assistantReply={assistantReply}
      />
    )}
  </>
)
}

export default App