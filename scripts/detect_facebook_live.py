#!/usr/bin/env python3
"""Read Facebook professional-profile videos using a private user token."""
import json, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

token=os.environ.get("FB_TOKEN","").strip()
if not token:
    raise SystemExit("Missing FB_TOKEN secret; leaving existing status untouched")
params=urllib.parse.urlencode({
    "type":"uploaded",
    "fields":"id,permalink_url,live_status,title,created_time",
    "limit":"10",
    "access_token":token,
})
url="https://graph.facebook.com/v26.0/me/videos?"+params
req=urllib.request.Request(url,headers={"User-Agent":"RAV-Facebook-Live/1.0"})
try:
    with urllib.request.urlopen(req,timeout=25) as resp:
        payload=json.load(resp)
    if not isinstance(payload.get("data"),list):
        raise ValueError("Unexpected Facebook response")
except Exception as exc:
    # Avoid printing URLs or access tokens in logs.
    raise SystemExit("Facebook API request failed; keeping last known status") from None

videos=payload["data"]
live=next((v for v in videos if v.get("live_status")=="LIVE" and str(v.get("id","")).isdigit()),None)
status={
    "live":bool(live),
    "videoId":str(live["id"]) if live else "",
    "title":str(live.get("title","")) if live else "",
    "checkedAt":datetime.now(timezone.utc).isoformat()
}
Path("facebook-live.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Facebook LIVE:", "active" if live else "inactive")
