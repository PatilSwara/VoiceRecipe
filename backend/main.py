import os
import logging
from typing import Literal

import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from youtube_transcript_api import (
    AgeRestricted,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApiException,
)

from models.recipe import NonEmptyText, Recipe
from services.cleaner import clean_transcript
from services.cooking_assistant import answer_cooking_question
from services.parser_llm import NoRecipeError, RecipeParseError, parse_recipe_with_llm
from services.safety_analyzer import SafetyParseError, analyze_recipe_safety
from services.transcript import get_transcript
from services.video_fallback import VideoFallbackError, get_video_cooking_notes, has_video_fallback
from utils.youtube import extract_video_id


MAX_TRANSCRIPT_CHARS = 16_000
logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    recipe: Recipe
    current_step: int = Field(ge=0)
    question: NonEmptyText


class TranscriptRequest(BaseModel):
    transcript: NonEmptyText

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {"message": "Recipe Voice App Backend Running"}

@app.post("/ask/")
def ask_question(data: AskRequest):
    if data.current_step >= len(data.recipe.steps):
        raise HTTPException(status_code=422, detail="Current step is outside this recipe.")
    try:
        answer = answer_cooking_question(
            recipe=data.recipe.model_dump(),
            current_step=data.current_step,
            question=data.question
        )
    except openai.OpenAIError:
        raise HTTPException(status_code=503, detail="AI service is currently busy or unavailable. Please try again later.")
    if not isinstance(answer, str) or not answer.strip():
        raise HTTPException(status_code=502, detail="The cooking assistant returned an empty answer. Please try again.")
    return {"answer": answer.strip()}

@app.get("/transcript/")
def transcript(url: str, mode: Literal["captions", "whisper"] = "captions"):

    video_id = extract_video_id(url)

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL"
        )

    if mode == "whisper":
        raise HTTPException(
            status_code=501,
            detail="Whisper fallback is currently disabled in this environment."
        )

    try:
        transcript_text = get_transcript(video_id)
    except RequestBlocked as error:
        logger.warning("YouTube blocked captions for %s: %s", video_id, type(error).__name__)
        if has_video_fallback():
            return build_recipe_from_video(video_id)
        raise HTTPException(
            status_code=503,
            detail="YouTube blocked caption requests from this server. Configure the free Gemini video fallback or paste the video's transcript."
        ) from error
    except (NoTranscriptFound, TranscriptsDisabled) as error:
        logger.info("Captions unavailable for %s: %s", video_id, type(error).__name__)
        if has_video_fallback():
            return build_recipe_from_video(video_id)
        raise HTTPException(
            status_code=422,
            detail="No accessible English captions were found for this video. You can paste a transcript below."
        ) from error
    except (VideoUnavailable, AgeRestricted) as error:
        logger.info("Video unavailable for %s: %s", video_id, type(error).__name__)
        raise HTTPException(
            status_code=400,
            detail="This video is unavailable or restricted. Try another video."
        ) from error
    except YouTubeTranscriptApiException as error:
        logger.warning("Caption retrieval failed for %s: %s", video_id, type(error).__name__)
        if has_video_fallback():
            return build_recipe_from_video(video_id)
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve this video's captions. Paste its transcript below or try another video."
        ) from error

    return build_recipe(transcript_text)


@app.post("/recipe-from-transcript/")
def recipe_from_transcript(data: TranscriptRequest):
    return build_recipe(data.transcript.splitlines())


def build_recipe_from_video(video_id):
    try:
        notes = get_video_cooking_notes(video_id)
    except VideoFallbackError as error:
        logger.warning("Gemini video fallback failed for %s: %s", video_id, type(error).__name__)
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    if notes.strip().upper() == "NO_RECIPE":
        raise HTTPException(status_code=422, detail="This video does not describe a cooking recipe.")
    return build_recipe(notes.splitlines())


def build_recipe(transcript_lines):
    cleaned_text = clean_transcript(transcript_lines)

    if not cleaned_text:
        raise HTTPException(status_code=422, detail="No usable captions were found for this video.")
    if sum(len(line) for line in cleaned_text) > MAX_TRANSCRIPT_CHARS:
        raise HTTPException(status_code=413, detail="This video's captions are too long for the free AI limit. Try a shorter video.")

    try:
        recipe = parse_recipe_with_llm(cleaned_text)
        safety_data = analyze_recipe_safety(recipe)
    except NoRecipeError:
        raise HTTPException(status_code=422, detail="The captions do not describe a usable cooking recipe. Try another video.")
    except RecipeParseError:
        raise HTTPException(status_code=502, detail="Could not build a usable recipe from this video's captions. Please try another video.")
    except SafetyParseError:
        raise HTTPException(status_code=502, detail="Could not check recipe safety. Please try again.")
    except openai.OpenAIError:
        raise HTTPException(status_code=503, detail="AI service is currently busy or unavailable. Please try again later.")

    return {**recipe.model_dump(), **safety_data.model_dump()}
