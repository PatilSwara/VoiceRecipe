from fastapi import FastAPI, HTTPException
from services.transcript import get_transcript
from utils.youtube import extract_video_id
from services.cleaner import clean_transcript
from services.parser_llm import parse_recipe_with_llm
from fastapi.middleware.cors import CORSMiddleware
from services.safety_analyzer import analyze_recipe_safety
from services.whisper_transcriber import transcribe_youtube_video
from services.cooking_assistant import (
    answer_cooking_question
)
from youtube_transcript_api import YouTubeTranscriptApiException

import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {"message": "Recipe Voice App Backend Running"}

@app.post("/ask/")
def ask_question(data: dict):

    answer = answer_cooking_question(
        recipe=data["recipe"],
        current_step=data["current_step"],
        question=data["question"]
    )

    return {
        "answer": answer
    }

@app.get("/transcript/")
def transcript(url: str, mode: str = "captions"):


    video_id = extract_video_id(url)

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL"
        )


    try:

        if mode == "whisper":

            print("Using Whisper transcription...")

            transcript_text = transcribe_youtube_video(url)

        else:

            print("Using YouTube captions...")

            transcript_text = get_transcript(video_id)

    except YouTubeTranscriptApiException as e:

        print(f"YouTube captions unavailable: {e}")


        transcript_text = transcribe_youtube_video(url)

    cleaned_text = clean_transcript(transcript_text)

    recipe = parse_recipe_with_llm(cleaned_text)
    
    if recipe.title == "Parsing Failed":
        raise HTTPException(
            status_code=500,
            detail="Failed to parse recipe from transcript."
        )

    safety_data = analyze_recipe_safety(recipe)
    return {
    **recipe.model_dump(),
    **safety_data.model_dump()
}
