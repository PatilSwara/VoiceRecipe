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

    output_template = f"{TEMP_FOLDER}/{audio_id}"

    ydl_opts = {

    "format": "bestaudio/best",

    "outtmpl": "temp_audio.%(ext)s",

    "quiet": True,

    "js_runtimes": {
        "node": "node"
    }
}

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