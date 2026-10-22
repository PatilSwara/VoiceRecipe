import { useCallback, useEffect, useRef, useState } from "react";
import { API_URL, readApiResponse } from "../api";

function CookingPage({ recipe, exitCookingMode }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [lastHeard, setLastHeard] = useState("");
  const [assistantReply, setAssistantReply] = useState("");
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [voiceError, setVoiceError] = useState("");

  const currentStepRef = useRef(0);
  const recognitionRef = useRef(null);
  const recognitionStateRef = useRef("idle");
  const voiceEnabledRef = useRef(false);
  const speakingRef = useRef(false);
  const activeRef = useRef(false);
  const speechIdRef = useRef(0);
  const requestIdRef = useRef(0);
  const requestControllerRef = useRef(null);

  const startListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (
      !recognition ||
      !activeRef.current ||
      !voiceEnabledRef.current ||
      speakingRef.current ||
      recognitionStateRef.current !== "idle"
    ) {
      return;
    }

    recognitionStateRef.current = "starting";
    try {
      recognition.start();
    } catch (error) {
      recognitionStateRef.current = "idle";
      if (error.name !== "InvalidStateError") {
        voiceEnabledRef.current = false;
        setVoiceEnabled(false);
        setVoiceError("Could not start voice commands. Check microphone access.");
      }
    }
  }, []);

  const pauseListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (
      !recognition ||
      recognitionStateRef.current === "idle" ||
      recognitionStateRef.current === "stopping"
    ) {
      return;
    }
    recognitionStateRef.current = "stopping";
    try {
      recognition.abort();
    } catch {
      recognitionStateRef.current = "idle";
    }
  }, []);

  const speakStep = useCallback((text) => {
    if (!activeRef.current || !text) return;
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
      setVoiceError("Speech playback is unavailable in this browser.");
      return;
    }

    const speechId = ++speechIdRef.current;
    speakingRef.current = true;
    pauseListening();
    window.speechSynthesis.cancel();

    const speech = new window.SpeechSynthesisUtterance(text);
    const selectedVoice = window.speechSynthesis
      .getVoices()
      .find((voice) => voice.lang === "en-US");
    if (selectedVoice) speech.voice = selectedVoice;
    speech.lang = "en-US";
    speech.rate = 0.9;

    const finishSpeech = () => {
      if (!activeRef.current || speechIdRef.current !== speechId) return;
      speakingRef.current = false;
      startListening();
    };
    speech.onend = finishSpeech;
    speech.onerror = finishSpeech;

    try {
      window.speechSynthesis.speak(speech);
    } catch {
      finishSpeech();
      setVoiceError("Speech playback failed. You can still use the step buttons.");
    }
  }, [pauseListening, startListening]);

  const nextStep = useCallback(() => {
    const next = currentStepRef.current + 1;
    if (next >= recipe.steps.length) return;
    currentStepRef.current = next;
    setCurrentStep(next);
    setAssistantReply("");
    requestIdRef.current += 1;
    requestControllerRef.current?.abort();
    speakStep(recipe.steps[next].instruction);
  }, [recipe.steps, speakStep]);

  const previousStep = useCallback(() => {
    const previous = currentStepRef.current - 1;
    if (previous < 0) return;
    currentStepRef.current = previous;
    setCurrentStep(previous);
    setAssistantReply("");
    requestIdRef.current += 1;
    requestControllerRef.current?.abort();
    speakStep(recipe.steps[previous].instruction);
  }, [recipe.steps, speakStep]);

  const askCookingQuestion = useCallback(async (question) => {
    requestControllerRef.current?.abort();
    const requestId = ++requestIdRef.current;
    const questionStep = currentStepRef.current;
    const controller = new AbortController();
    requestControllerRef.current = controller;

    try {
      const response = await fetch(API_URL + "/ask/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipe,
          current_step: questionStep,
          question,
        }),
        signal: controller.signal,
      });
      const data = await readApiResponse(response, "The cooking assistant is unavailable. Please try again.");
      if (typeof data.answer !== "string" || !data.answer.trim()) {
        throw new Error("The cooking assistant returned an empty answer. Please try again.");
      }
      if (
        !activeRef.current ||
        requestIdRef.current !== requestId ||
        currentStepRef.current !== questionStep
      ) {
        return;
      }
      setAssistantReply(data.answer);
      speakStep(data.answer);
    } catch (error) {
      if (controller.signal.aborted || !activeRef.current || requestIdRef.current !== requestId) {
        return;
      }
      const message = error instanceof TypeError
        ? "Could not reach the backend. Check the API server and try again."
        : error.message || "Could not reach the cooking assistant.";
      setAssistantReply(message);
      speakStep(message);
    } finally {
      if (requestControllerRef.current === controller) {
        requestControllerRef.current = null;
      }
    }
  }, [recipe, speakStep]);

  const handleTranscript = useCallback((transcript) => {
    const command = transcript
      .toLowerCase()
      .trim()
      .replace(/[.,!?]+$/g, "")
      .replace(/\s+/g, " ");

    if (["next", "next step", "go to next step"].includes(command)) {
      nextStep();
    } else if (["previous", "previous step", "go back", "back"].includes(command)) {
      previousStep();
    } else if (["repeat", "repeat step", "repeat that"].includes(command)) {
      speakStep(recipe.steps[currentStepRef.current].instruction);
    } else if (["exit", "exit cooking mode", "stop cooking"].includes(command)) {
      exitCookingMode();
    } else {
      askCookingQuestion(transcript);
    }
  }, [askCookingQuestion, exitCookingMode, nextStep, previousStep, recipe.steps, speakStep]);

  function toggleVoiceCommands() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceError("Speech recognition is unavailable in this browser. Use the step buttons.");
      return;
    }
    const enabled = !voiceEnabled;
    voiceEnabledRef.current = enabled;
    setVoiceEnabled(enabled);
    setVoiceError("");
  }

  useEffect(() => {
    activeRef.current = true;
    let effectActive = true;
    queueMicrotask(() => {
      if (effectActive) speakStep(recipe.steps[0].instruction);
    });

    return () => {
      effectActive = false;
      activeRef.current = false;
      voiceEnabledRef.current = false;
      speakingRef.current = false;
      speechIdRef.current += 1;
      requestIdRef.current += 1;
      requestControllerRef.current?.abort();
      window.speechSynthesis?.cancel();
    };
  }, [recipe.steps, speakStep]);

  useEffect(() => {
    if (!voiceEnabled) return undefined;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return undefined;

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognitionStateRef.current = "idle";
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      recognitionStateRef.current = "listening";
    };
    recognition.onend = () => {
      recognitionStateRef.current = "idle";
      startListening();
    };
    recognition.onerror = (event) => {
      if (["not-allowed", "service-not-allowed", "audio-capture", "network"].includes(event.error)) {
        voiceEnabledRef.current = false;
        setVoiceEnabled(false);
        setVoiceError("Voice commands stopped. Check microphone permission and connection.");
      }
    };
    recognition.onresult = (event) => {
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        if (!result.isFinal) continue;
        const transcript = result[0]?.transcript?.trim();
        if (transcript) {
          setLastHeard(transcript);
          handleTranscript(transcript);
        }
      }
    };

    let effectActive = true;
    queueMicrotask(() => {
      if (effectActive) startListening();
    });
    return () => {
      effectActive = false;
      if (recognitionRef.current === recognition) {
        recognitionRef.current = null;
      }
      recognition.onstart = null;
      recognition.onend = null;
      recognition.onerror = null;
      recognition.onresult = null;
      recognitionStateRef.current = "idle";
      try {
        recognition.abort();
      } catch {
        // The recognition session may already be closed.
      }
    };
  }, [handleTranscript, startListening, voiceEnabled]);

  return (
    <div className="cooking-mode">
      <h2>Cooking Mode</h2>
      <p>Step {currentStep + 1} of {recipe.steps.length}</p>
      <div className="step-card">
        <h3>Step {recipe.steps[currentStep].step_number}</h3>
        <p>{recipe.steps[currentStep].instruction}</p>
      </div>

      <button
        onClick={toggleVoiceCommands}
        aria-pressed={voiceEnabled}
        style={{ backgroundColor: voiceEnabled ? "#d32f2f" : "" }}
      >
        {voiceEnabled ? "Disable Voice Commands" : "Enable Voice Commands"}
      </button>
      {voiceError && <p role="alert">{voiceError}</p>}

      <div className="controls">
        <button onClick={previousStep} disabled={currentStep === 0}>Previous</button>
        <button onClick={() => speakStep(recipe.steps[currentStep].instruction)}>Repeat</button>
        <button onClick={nextStep} disabled={currentStep === recipe.steps.length - 1}>Next</button>
      </div>

      <div className="conversation-box">
        <h3>Voice Assistant</h3>
        {lastHeard && <p><strong>You said:</strong> {lastHeard}</p>}
        {assistantReply && <p><strong>Assistant:</strong> {assistantReply}</p>}
      </div>

      <button className="exit-button" onClick={exitCookingMode}>Exit Cooking Mode</button>
    </div>
  );
}

export default CookingPage;
