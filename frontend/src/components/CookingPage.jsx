import { useState, useEffect, useRef } from "react";

function CookingPage({ recipe, exitCookingMode }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [lastHeard, setLastHeard] = useState("");
  const [assistantReply, setAssistantReply] = useState("");
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  
  const currentStepRef = useRef(0);
  const recognitionRef = useRef(null);

  const voiceEnabledRef = useRef(voiceEnabled);
  useEffect(() => {
    voiceEnabledRef.current = voiceEnabled;
  }, [voiceEnabled]);

  // Initialize speech synthesis and read first step on mount
  useEffect(() => {
    if (window.speechSynthesis.getVoices().length === 0) {
      window.speechSynthesis.onvoiceschanged = () => {
        speakStep(recipe.steps[0].instruction);
        window.speechSynthesis.onvoiceschanged = null;
      };
    } else {
      speakStep(recipe.steps[0].instruction);
    }

    return () => {
      window.speechSynthesis.cancel();
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function speakStep(text) {
    window.speechSynthesis.cancel();
    
    // Pause recognition while speaking to prevent feedback loop
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    setTimeout(() => {
      const speech = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      const selectedVoice = voices.find((voice) => voice.lang === "en-US");
      if (selectedVoice) speech.voice = selectedVoice;
      speech.lang = "en-US";
      speech.rate = 0.9;
      
      speech.onend = () => {
        // Restart recognition if it was enabled
        if (voiceEnabledRef.current && recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {
            console.error("Failed to restart recognition after speaking", e);
          }
        }
      };

      window.speechSynthesis.speak(speech);
    }, 50);
  }

  function nextStep() {
    const current = currentStepRef.current;
    if (current < recipe.steps.length - 1) {
      const next = current + 1;
      currentStepRef.current = next;
      setCurrentStep(next);
      speakStep(recipe.steps[next].instruction);
    }
  }

  function previousStep() {
    const current = currentStepRef.current;
    if (current > 0) {
      const previous = current - 1;
      currentStepRef.current = previous;
      setCurrentStep(previous);
      speakStep(recipe.steps[previous].instruction);
    }
  }

  async function askCookingQuestion(question) {
    try {
      const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${API_URL}/ask/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          recipe: recipe,
          current_step: currentStepRef.current,
          question: question,
        }),
      });
      const data = await response.json();
      setAssistantReply(data.answer);
      speakStep(data.answer);
    } catch (error) {
      console.error(error);
      setAssistantReply("Sorry, I could not reach the server.");
      speakStep("Sorry, I could not reach the server.");
    }
  }

  function toggleVoiceCommands() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition not supported in this browser.");
      return;
    }
    setVoiceEnabled(!voiceEnabled);
  }

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    if (voiceEnabled) {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.continuous = true;

      recognition.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
        setLastHeard(transcript);

        if (transcript.includes("next")) {
          nextStep();
          setAssistantReply("");
        } else if (transcript.includes("previous")) {
          previousStep();
          setAssistantReply("");
        } else if (transcript.includes("repeat")) {
          speakStep(recipe.steps[currentStepRef.current].instruction);
          setAssistantReply("");
        } else if (transcript.includes("exit")) {
          exitCookingMode();
        } else {
          askCookingQuestion(transcript);
        }
      };

      recognition.onend = () => {
        // Restart only if we still want voice enabled
        if (voiceEnabled) {
          try {
            recognition.start();
          } catch (e) {
            console.error("Failed to restart recognition", e);
          }
        }
      };

      try {
        recognition.start();
      } catch (e) {
        console.error(e);
      }
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.onend = null; // Prevent restart
        recognitionRef.current.stop();
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
      }
    };
  }, [voiceEnabled]); 

  return (
    <div className="cooking-mode">
      <h2>Cooking Mode</h2>
      <p>
        Step {currentStep + 1} of {recipe.steps.length}
      </p>

      <div className="step-card">
        <h3>Step {recipe.steps[currentStep].step_number}</h3>
        <p>{recipe.steps[currentStep].instruction}</p>
      </div>

      <button onClick={toggleVoiceCommands} style={{backgroundColor: voiceEnabled ? '#d32f2f' : ''}}>
        {voiceEnabled ? "Disable Voice Commands" : "Enable Voice Commands"}
      </button>

      <div className="controls">
        <button onClick={previousStep}>Previous</button>
        <button onClick={() => speakStep(recipe.steps[currentStep].instruction)}>
          Repeat
        </button>
        <button onClick={nextStep}>Next</button>
      </div>
      
      <div className="conversation-box">
        <h3>Voice Assistant</h3>
        {lastHeard && (
          <p>
            <strong>You said:</strong> {lastHeard}
          </p>
        )}
        {assistantReply && (
          <p>
            <strong>Assistant:</strong> {assistantReply}
          </p>
        )}
      </div>
      
      <button className="exit-button" onClick={exitCookingMode}>
        Exit Cooking Mode
      </button>
    </div>
  );
}

export default CookingPage;