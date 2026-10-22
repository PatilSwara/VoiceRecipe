import re


NOISE_MARKERS = re.compile(r"\[(?:music|applause)\]", re.IGNORECASE)
LEADING_TIMESTAMP = re.compile(r"^(?:\d{1,2}:)?\d{1,2}:\d{2}\s*")


def clean_transcript(lines):
    cleaned_lines = []
    for line in lines:
        spoken_text = NOISE_MARKERS.sub("", line).strip()
        spoken_text = LEADING_TIMESTAMP.sub("", spoken_text).strip()
        if spoken_text:
            cleaned_lines.append(spoken_text)
    return cleaned_lines
