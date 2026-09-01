COOKING_KEYWORDS = [
    "mix",
    "boil",
    "cook",
    "bake",
    "add",
    "stir",
    "heat",
    "milk",
    "sugar",
    "salt",
    "egg",
    "flour",
    "water",
    "oil",
    "pepper",
    "minutes",
    "refrigerator",
    "oven"
]


def clean_transcript(lines):

    cleaned_lines = []

    for line in lines:

        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip tiny fragments
        if len(line) < 10:
            continue

        # Remove subtitle noise
        if "[Music]" in line:
            continue

        if "[Applause]" in line:
            continue

        cleaned_lines.append(line)

    return cleaned_lines