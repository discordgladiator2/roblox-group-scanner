from urllib.parse import urlsplit
from datetime import datetime
import http.client
import json

def send_webhook(url, content=None, embeds=[]):
    data = json.dumps({"content": content, "embeds": embeds})
    p = urlsplit(url)
    conn = http.client.HTTPSConnection(p.hostname, p.port or 443)
    conn.request(
        method="POST",
        url=p.path + (f"?" + p.query if p.query else ""),
        body=data,
        headers={"Content-Type": "application/json"}
    )
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status >= 200

def embed_from_group(data):
    return dict(
        title="Found claimable group",
        url=f"https://www.roblox.com/groups/{data['id']}/--",
        fields=[
            dict(name="Group Id", value=data["id"]),
            dict(name="Group Name", value=data["name"]),
            dict(name="Group Members", value=data.get("memberCount", "?"))
        ],
        timestamp=datetime.now().isoformat()
    )