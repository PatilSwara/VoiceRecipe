function CookingPage({

  recipe,

  currentStep,

  previousStep,
  nextStep,

  speakStep,

  startVoiceCommands,

  exitCookingMode,

  lastHeard,
  assistantReply

}) {
    return (
        <div className="cooking-mode">

          <h2>Cooking Mode</h2>

          <p>
            Step {currentStep + 1}
            {" "}
            of
            {" "}
            {recipe.steps.length}
          </p>

          <div className="step-card">

            <h3>
              Step {recipe.steps[currentStep].step_number}
            </h3>

            <p>
              {recipe.steps[currentStep].instruction}
            </p>

          </div>

          <button onClick={startVoiceCommands}>
            Enable Voice Commands
          </button>

          <div className="controls">

            <button onClick={previousStep}>
              Previous
            </button>

            <button
              onClick={() =>
                speakStep(
                  recipe.steps[currentStep].instruction
                )
              }
            >
              Repeat
            </button>

            <button onClick={nextStep}>
              Next
            </button>

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
          <button
            className="exit-button"
            onClick={exitCookingMode}
          >
            Exit Cooking Mode
          </button>

        </div>
    )
}export default CookingPage