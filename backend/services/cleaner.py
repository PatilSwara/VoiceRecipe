import re


NOISE_MARKERS = re.compile(r"\[(?:music|applause)\]", re.IGNORECASE)


def clean_transcript(lines):
    cleaned_lines = []
    for line in lines:
        spoken_text = NOISE_MARKERS.sub("", line).strip()
        if spoken_text:
            cleaned_lines.append(spoken_text)
    return cleaned_lines
