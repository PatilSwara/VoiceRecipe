from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id):

    api = YouTubeTranscriptApi()

    transcript = api.fetch(video_id)

    transcript_lines = []

    for item in transcript:
        transcript_lines.append(item.text)

    return transcript_lines