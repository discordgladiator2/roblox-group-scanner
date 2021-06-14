from utils import send_webhook, embed_from_group
import socket
import ssl
import json
import logging
import traceback
logging.getLogger().setLevel(logging.CRITICAL)

def scanner_func(worker_num, thread_num, thread_barrier, thread_event,
                 gid_counter, gid_range, gid_lock, gid_ignore,
                 webhook_url, local_counter, proxies=None):
    ssl_context = ssl.create_default_context()
    thread_barrier.wait()
    thread_event.wait()

    while True:
        proxy_addr = proxies and next(proxies) or None
        sock = None

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            if proxy_addr:
                sock.connect(proxy_addr)
                sock.send(b"CONNECT groups.roblox.com:443 HTTP/1.1\r\n\r\n")
                sock.recv(1024**2)
            else:
                sock.connect(("groups.roblox.com", 443))
            sock = ssl_context.wrap_socket(sock, server_hostname="groups.roblox.com")
            
        except Exception as err:
            logging.warning(f"Couldn't establish connection (proxy {proxy_addr}): {err!r}")
            if sock:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()
            continue

        while True:
            with gid_lock:
                gid = gid_range[0] + (next(gid_counter) % (gid_range[1]-gid_range[0]))
            
            if gid in gid_ignore:
                continue
            
            try:
                sock.send(f"GET /v1/groups/{gid} HTTP/1.1\r\nHost: groups.roblox.com\r\n\r\n".encode())
                resp = sock.recv(1024**2)

                # ratelimited / ip blocked
                if resp.startswith(b"HTTP/1.1 429") or resp.startswith(b"HTTP/1.1 403"):
                    break

                # invalid group
                if resp.startswith(b"HTTP/1.1 400"):
                    gid_ignore[gid] = True
                    local_counter.count()
                    continue
                
                # server error
                if resp.startswith(b"HTTP/1.1 500"):
                    continue

                # successful response
                if resp.startswith(b"HTTP/1.1 200"):
                    data = json.loads(resp.split(b"\r\n\r\n", 1)[1])
                    local_counter.count()
                    
                    # claimable group
                    if not data.get("owner") and data.get("publicEntryAllowed") and not data.get("isLocked"):
                        gid_ignore[gid] = True
                        print(f"\r{data['id']} - {data['name']} - {data['memberCount']}" + (" " * 30), end="\n")
                        # send webhook, if url is specified
                        if webhook_url:
                            send_webhook(webhook_url, embeds=[embed_from_group(data)])

                    # no owner and no public entry / is locked
                    elif data.get("isLocked") or (not data.get("owner") and not data.get("publicEntryAllowed")):
                        gid_ignore[gid] = True
                    
                    continue
                
                # unrecognized
                raise Exception(
                    f"Unrecognized statusline while reading response: {resp[:20]}")

            except Exception as err:
                logging.warning(f"Dropping connection due to error: {err!r}")
                break
    
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()
        