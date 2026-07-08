def parse_recipe(lines):

    cleaned_steps = []

    for index, line in enumerate(lines):

        cleaned_steps.append({
            "step_number": index + 1,
            "instruction": line
        })

    return {
        "title": "Recipe",
        "steps": cleaned_steps
    }