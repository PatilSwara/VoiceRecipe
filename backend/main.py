from fastapi import FastAPI, HTTPException
from services.transcript import get_transcript
from utils.youtube import extract_video_id
from services.cleaner import clean_transcript
from services.parser_llm import parse_recipe_with_llm
from fastapi.middleware.cors import CORSMiddleware
from services.safety_analyzer import analyze_recipe_safety
from services.whisper_transcriber import transcribe_youtube_video
from fastapi.responses import Response
from services.tts_service import generate_speech
from services.cooking_assistant import (
    answer_cooking_question
)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {"message": "Recipe Voice App Backend Running"}
@app.post("/speak/")
def speak(data: dict):

    text = data["text"]

    audio = generate_speech(text)

    return Response(
        content=audio,
        media_type="audio/mpeg"
    )

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

    except Exception:

        print("YouTube captions unavailable.")


        transcript_text = transcribe_youtube_video(url)

    cleaned_text = clean_transcript(transcript_text)

    recipe = parse_recipe_with_llm(cleaned_text)
    safety_data = analyze_recipe_safety(recipe)
    return {
    **recipe.model_dump(),
    **safety_data.model_dump()
}
