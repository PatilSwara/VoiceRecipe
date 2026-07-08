import json
import os

from openai import OpenAI
from models.recipe import SafetyAnalysis

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def analyze_recipe_safety(recipe):

    prompt = f"""
You are a cooking safety assistant.

Analyze this recipe and identify:

1. Cooking hazards
2. Safety precautions
3. First aid information if accidents occur

Focus especially on:
- hot sugar
- microwaves
- knives
- frying oil
- steam
- ovens
- burns
- raw meat
- dangerous materials
- fire risks
Only include hazards that are DIRECTLY relevant to this specific recipe.

Do NOT include generic kitchen safety advice.

Do NOT mention:
- knives unless knives are actually used
- raw meat unless raw meat is present
- fire risks unless there is meaningful fire danger
- equipment not used in the recipe

Warnings must be specific, practical, and tied to actual recipe steps or cooking methods.
Return ONLY valid JSON.

FORMAT:
{{
  "safety_warnings": [
    {{
      "type": "Microwave Safety",
      "warning": "Do not use metal utensils in the microwave."
    }}
  ],

  "first_aid": [
    {{
      "situation": "Sugar Burn",
      "response": "Cool the burn under running water for at least 20 minutes."
    }}
  ]
}}

Recipe:
{json.dumps(recipe.model_dump(), indent=2)}
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
        safety_data = json.loads(text_response)

        validated_safety = SafetyAnalysis(**safety_data)

        return validated_safety

    except json.JSONDecodeError:

        return SafetyAnalysis(
        safety_warnings=[],
        first_aid=[]
)