import json
from pydantic import ValidationError

from models.recipe import Recipe
from services.groq_client import GROQ_MODEL, get_client


class RecipeParseError(ValueError):
    pass


class NoRecipeError(RecipeParseError):
    pass


def parse_recipe_with_llm(transcript_lines):

    transcript_text = "\n".join(transcript_lines)

    prompt = f"""
You are an AI cooking assistant.

Your task:
Understand the cooking process from the transcript and reconstruct a COMPLETE and COHERENT recipe.

Do NOT simply copy transcript lines.

You should:
- infer missing context when obvious
- combine fragmented instructions
- rewrite unclear transcript sections into proper cooking instructions
- preserve logical cooking order
- correct obvious transcript spelling mistakes
- normalize ingredient and cooking terminology
- infer likely ingredient names from context
- use standard culinary terminology whenever possible
- do not invent a recipe when the transcript has no cooking instructions

If the transcript does not describe preparing food or drink, return ONLY
{{"error": "not_a_recipe"}}. Do not guess ingredients or steps.

Difficulty should be determined realistically based on:
- cooking techniques required
- timing precision
- temperature control
- risk level
- preparation complexity
- skill required

Ignore:
- greetings
- jokes
- sponsorships
- audience interaction
- storytelling
- unrelated commentary

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanations
- No extra text

The recipe should feel like a proper recipe written by a human.

JSON FORMAT:
{{
  "title": "Recipe Title",

  "estimated_time": "30 minutes",

  "difficulty": "Easy",

  "equipment": [
    "Pan"
  ],

  "ingredients": [
    {{
      "name": "Milk",
      "quantity": "3 cups"
    }}
  ],

  "steps": [
    {{
      "step_number": 1,
      "instruction": "Pour the milk into a pan and bring it to a boil."
    }}
  ]
}}

Transcript:
{transcript_text}
"""

    response = get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    try:
        text_response = response.choices[0].message.content
        recipe_data = json.loads(text_response or "")
        if isinstance(recipe_data, dict) and recipe_data.get("error") == "not_a_recipe":
            raise NoRecipeError("The captions do not describe a recipe.")
        recipe = Recipe.model_validate(recipe_data)
    except (IndexError, AttributeError, TypeError, json.JSONDecodeError, ValidationError) as error:
        raise RecipeParseError("The AI returned an unusable recipe.") from error

    for number, step in enumerate(recipe.steps, start=1):
        step.step_number = number
    return recipe
