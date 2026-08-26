import os
import uuid

import yt_dlp

from faster_whisper import WhisperModel


model = WhisperModel(
    "base",
    compute_type="int8"
)


TEMP_FOLDER = "temp_audio"

os.makedirs(TEMP_FOLDER, exist_ok=True)


def transcribe_youtube_video(video_url):

    audio_id = str(uuid.uuid4())

    output_template = f"{TEMP_FOLDER}/{audio_id}.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True
    }

    downloaded_file = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(video_url, download=True)

            downloaded_file = ydl.prepare_filename(info)

        segments, info = model.transcribe(
            downloaded_file,
            beam_size=5
        )

        transcript_lines = []

        for segment in segments:
            transcript_lines.append(segment.text)

        return transcript_lines
    finally:
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)