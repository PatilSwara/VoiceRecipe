from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    parsed_url = urlparse(url)

    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]

    if parsed_url.hostname in (
        "www.youtube.com",
        "youtube.com"
    ):
        if parsed_url.path.startswith("/shorts/"):
            return parsed_url.path.split("/")[2]
        query = parse_qs(parsed_url.query)
        if "v" in query:
            return query["v"][0]

    return None