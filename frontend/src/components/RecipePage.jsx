function RecipePage({
  recipe,
  startCooking,
  tryAnotherVideo
}) {

  return (
        <div className="recipe-container">

          <h2>{recipe.title}</h2>
          <p>AI-generated recipe and safety guidance. Check the original video before cooking.</p>

          <p>
            <strong>Estimated Time:</strong>
            {" "}
            {recipe.estimated_time}
          </p>

          <p>
            <strong>Difficulty:</strong>
            {" "}
            {recipe.difficulty}
          </p>

          <h3>Equipment</h3>
          {recipe.equipment.length === 0 ? <p>None listed.</p> : (
            <ul>
              {recipe.equipment.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          )}

          <h3>Ingredients</h3>

          <ul>
            {recipe.ingredients.map((ingredient, index) => (
              <li key={index}>
                {ingredient.quantity} - {ingredient.name}
              </li>
            ))}
          </ul>

          <h3>Steps</h3>

          <ol>
            {recipe.steps.map((step) => (
              <li key={step.step_number}>
                {step.instruction}
              </li>
            ))}
          </ol>

          <h3>Safety Warnings</h3>
          {recipe.safety_warnings.length === 0 ? <p>None identified for this recipe.</p> : (
            <ul>
              {recipe.safety_warnings.map((warning, index) => (
                <li key={index}>
                  <strong>{warning.type}:</strong>
                  {" "}
                  {warning.warning}
                </li>
              ))}
            </ul>
          )}
          
          <h3>First Aid</h3>
          {recipe.first_aid.length === 0 ? <p>None identified for this recipe.</p> : (
            <ul>
              {recipe.first_aid.map((aid, index) => (
                <li key={index}>
                  <strong>{aid.situation}:</strong>
                  {" "}
                  {aid.response}
                </li>
              ))}
            </ul>
          )}
          <button
            className="start-button"
            onClick={startCooking}
          >
            Start Cooking
          </button>
          <button onClick={tryAnotherVideo}>Try Another Video</button>

        </div>
  )
}
export default RecipePage
