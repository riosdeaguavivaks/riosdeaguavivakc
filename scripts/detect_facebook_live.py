
#!/usr/bin/env python3
"""RAV Facebook LIVE detector."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime, timezone
from pathlib import Path


# Facebook access token stored securely in GitHub
token = os.environ.get("FB_TOKEN", "").strip()

if not token:
    raise SystemExit(
        "Missing FB_TOKEN secret; leaving existing status untouched"
    )


# Facebook Graph API request
params = urllib.parse.urlencode({
    "type": "uploaded",
    "fields": "id,permalink_url,live_status,title,created_time",
    "limit": "10",
    "access_token": token,
})

url = "https://graph.facebook.com/v26.0/me/videos?" + params

request = urllib.request.Request(
    url,
    headers={"User-Agent": "RAV-Facebook-Live/1.0"}
)


# Connect to Facebook
try:
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.load(response)

    if not isinstance(payload.get("data"), list):
        raise ValueError("Unexpected Facebook response")


# Facebook returned an HTTP error
except urllib.error.HTTPError as exc:
    try:
        error_data = json.loads(exc.read().decode("utf-8"))
        fb_error = error_data.get("error", {})

        error_code = fb_error.get("code", "unknown")
        error_subcode = fb_error.get("error_subcode", "none")
        error_type = fb_error.get("type", "unknown")

    except (ValueError, UnicodeError, AttributeError):
        error_code = "unknown"
        error_subcode = "none"
        error_type = "unknown"

    raise SystemExit(
        f"Facebook API request failed: HTTP {exc.code}; "
        f"error code: {error_code}; "
        f"subcode: {error_subcode}; "
        f"type: {error_type}; "
        "keeping last known status"
    ) from None


# Network error
except urllib.error.URLError as exc:
    raise SystemExit(
        "Facebook API network error: "
        f"{type(exc.reason).__name__}; "
        "keeping last known status"
    ) from None


# Other unexpected errors
except Exception as exc:
    raise SystemExit(
        "Facebook API request failed: "
        f"{type(exc).__name__}; "
        "keeping last known status"
    ) from None


# Search for an active Facebook LIVE video
videos = payload["data"]

live_video = next(
    (
        video
        for video in videos
        if video.get("live_status") == "LIVE"
        and str(video.get("id", "")).isdigit()
    ),
    None
)


# Prepare LIVE status
status = {
    "live": bool(live_video),
    "videoId": str(live_video["id"]) if live_video else "",
    "title": str(live_video.get("title", "")) if live_video else "",
    "checkedAt": datetime.now(timezone.utc).isoformat()
}


# Save the result
Path("facebook-live.json").write_text(
    json.dumps(
        status,
        ensure_ascii=False,
        indent=2
    ) + "\n",
    encoding="utf-8"
)


# Safe diagnostic output
print(
    "Facebook LIVE:",
    "active" if live_video else "inactive"
)

if live_video:
    print("Facebook video ID:", live_video["id"])
