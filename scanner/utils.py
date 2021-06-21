from urllib.parse import urlsplit
from datetime import datetime, timezone
import socket
import ssl
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
    return resp.status in (200, 204)

def embed_from_group(data, funds=None):
    return dict(
        title="Found claimable group",
        url=f"https://www.roblox.com/groups/{data['id']}/--",
        fields=[
            dict(name="Group Id", value=data["id"]),
            dict(name="Group Name", value=data["name"]),
            dict(name="Group Members", value=data.get("memberCount", "?")),
            dict(name="Group Funds", value=f"{f'R$ {funds}' if funds is not None else '?'}")
        ],
        timestamp=datetime.now(timezone.utc).isoformat()
    )

def get_group_funds(group_id, proxy_addr=None, timeout=5.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    if proxy_addr:
        sock.connect(proxy_addr)
        sock.send(b"CONNECT economy.roblox.com:443 HTTP/1.1\r\n\r\n")
        sock.recv(1024**2)
    else:
        sock.connect(("economy.roblox.com", 443))
    sock = ssl.create_default_context().wrap_socket(sock, server_hostname="economy.roblox.com")
    
    sock.send(f"GET /v1/groups/{group_id}/currency HTTP/1.1\r\nHost: economy.roblox.com\r\n\r\n".encode())
    resp = sock.recv(1024**2)

    if resp.startswith(b"HTTP/1.1 200"):
        data = json.loads(resp.split(b"\r\n\r\n", 1)[1])
        return data.get("robux")
    
    # funds are not public
    if resp.startswith(b"HTTP/1.1 403") and b"code\":3" in resp:
        return

    raise Exception(f"Unrecognized statusline: {resp[:20]}")