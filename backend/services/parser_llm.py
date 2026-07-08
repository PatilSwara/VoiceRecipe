import json
import os
from pathlib import Path
from models.recipe import Recipe
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    text_response = response.choices[0].message.content.strip()

    text_response = text_response.replace("```json", "")
    text_response = text_response.replace("```", "")

    try:

        recipe_data = json.loads(text_response)

        recipe = Recipe(**recipe_data)

        return recipe

    except (json.JSONDecodeError, ValidationError):

        return Recipe(
            title="Parsing Failed",
            estimated_time="Unknown",
            difficulty="Unknown",
            equipment=[],
            ingredients=[],
            steps=[]
        )