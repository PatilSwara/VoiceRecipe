import os
import requests

from dotenv import load_dotenv

load_dotenv()


ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

VOICE_ID = "PIGsltMj3gFMR34aFDI3"


def generate_speech(text):

    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/"
        f"{VOICE_ID}"
    )

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }

    response = requests.post(
        url,
        json=data,
        headers=headers
    )
    return response.content