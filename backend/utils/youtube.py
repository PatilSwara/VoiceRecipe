import re
from urllib.parse import parse_qs, urlparse


VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")

def extract_video_id(url):
    parsed_url = urlparse(url.strip())
    if parsed_url.scheme not in ("http", "https"):
        return None

    if parsed_url.hostname == "youtu.be":
        candidate = parsed_url.path.strip("/")
    elif parsed_url.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        path_parts = parsed_url.path.strip("/").split("/")
        if path_parts == ["watch"]:
            candidate = parse_qs(parsed_url.query).get("v", [""])[0]
        elif len(path_parts) == 2 and path_parts[0] in ("shorts", "live", "embed"):
            candidate = path_parts[1]
        else:
            return None
    else:
        return None

    return candidate if VIDEO_ID.fullmatch(candidate) else None
