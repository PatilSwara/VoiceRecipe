"""Use Gemini's public YouTube video input when caption scraping is blocked."""

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

GEMINI_VIDEO_MODEL = os.getenv("GEMINI_VIDEO_MODEL", "gemini-3.8-flash")
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_VIDEO_MODEL}:generateContent"
)
VIDEO_PROMPT = (
    "Describe only the cooking information actually present in this video. "
    "List the dish, ingredients and quantities, equipment, preparation steps, "
    "cooking times, and temperatures in their original order. Include useful "
    "details shown visually if they are clear. Do not guess missing quantities "
    "or invent steps. Ignore introductions, ads, and unrelated speech. "
    "If the video does not show how to prepare food or drink, reply NO_RECIPE. "
    "Keep your answer under 1500 words."
)


class VideoFallbackError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def has_video_fallback():
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def get_video_cooking_notes(video_id):
    """Ask Gemini to read a public video; return notes for the recipe parser."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise VideoFallbackError("Automatic video fallback is not configured.", 503)

    payload = {
        "contents": [{
            "parts": [
                {"text": VIDEO_PROMPT},
                {"file_data": {"file_uri": f"https://www.youtube.com/watch?v={video_id}"}},
            ]
        }],
        "generationConfig": {
            "maxOutputTokens": 3000,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }
    request = Request(
        GEMINI_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            result = json.load(response)
    except HTTPError as error:
        if error.code == 400:
            raise VideoFallbackError(
                "This video could not be analyzed by the configured Gemini model. Try another public video or paste its transcript.",
                422,
            ) from error
        if error.code == 404:
            raise VideoFallbackError(
                "The configured Gemini video model is unavailable. Check GEMINI_VIDEO_MODEL.",
                503,
            ) from error
        if error.code == 403:
            raise VideoFallbackError(
                "The Gemini video key was rejected. Check GEMINI_API_KEY in the backend settings.",
                503,
            ) from error
        if error.code == 429:
            raise VideoFallbackError(
                "The free video analysis limit was reached. Please try again later.", 503
            ) from error
        raise VideoFallbackError(
            "Video analysis is unavailable. Please try again later or paste the transcript.", 503
        ) from error
    except (OSError, URLError, ValueError) as error:
        raise VideoFallbackError(
            "Video analysis is unavailable. Please try again later or paste the transcript.", 503
        ) from error

    try:
        parts = result["candidates"][0]["content"]["parts"]
        notes = "\n".join(part["text"] for part in parts if part.get("text"))
    except (KeyError, IndexError, TypeError) as error:
        raise VideoFallbackError("Video analysis returned no usable cooking details.") from error
    if not notes.strip():
        raise VideoFallbackError("Video analysis returned no usable cooking details.")
    return notes.strip()
