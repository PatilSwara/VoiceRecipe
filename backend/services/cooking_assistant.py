import json

from services.groq_client import GROQ_MODEL, get_client


def answer_cooking_question(
    recipe,
    current_step,
    question
):

    prompt = f"""
You are an AI cooking assistant.

Answer the user's question using ONLY
the recipe information provided.

Rules:
- Keep answers concise
- Do not invent ingredients
- Do not invent instructions
-Use reasonable contextual understanding of the current cooking step.

-If the user asks a follow-up question,
infer what part of the current step
they are referring to and answer the question.
-For example, if the current instruction is "Add a few drops of water to the pan, cover with a lid, and cook for 7 to 10 minutes over low heat" , 
and the user asks how many minutes, answer with "7 to 10 minutes"
-Only say you do not know if the recipe
truly lacks the information.

Recipe:
{json.dumps(recipe, indent=2)}

Current Step Number:
{current_step + 1}

Current Step Instruction:
{recipe["steps"][current_step]["instruction"]}

User Question:
{question}
"""
    response = get_client().chat.completions.create(
        model=GROQ_MODEL,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.2
    )

    try:
        return response.choices[0].message.content
    except (IndexError, AttributeError, TypeError):
        return None
