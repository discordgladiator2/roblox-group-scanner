from utils import send_webhook, embed_from_group, get_group_funds
import socket
import ssl
import json
import logging
import traceback
logging.getLogger().setLevel(logging.CRITICAL)

def scanner_func(worker_num, thread_num, thread_barrier, thread_event,
                 gid_counter, gid_range, gid_lock, gid_ignore,
                 webhook_url, local_counter, proxies,
                 min_funds, min_members,
                 timeout):
    ssl_context = ssl.create_default_context()
    thread_barrier.wait()
    thread_event.wait()

    retry_gid = None

    while True:
        proxy_addr = proxies and next(proxies) or None
        sock = None

        # establish connection to groups.roblox.com
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
            logging.warning(
                f"Couldn't establish connection to groups.roblox.com (proxy {proxy_addr}): {err!r}")
            if sock:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()
            continue
        
        # scan for claimable groups matching criteria
        while True:
            if retry_gid:
                gid = retry_gid
                retry_gid = None
            else:
                with gid_lock:
                    gid = gid_range[0] + next(gid_counter) % (gid_range[1] - gid_range[0])
                
            # skip previously ignored groups
            if gid in gid_ignore:
                continue
            
            try:
                # send request and read response
                sock.send(f"GET /v1/groups/{gid} HTTP/1.1\r\nHost: groups.roblox.com\r\n\r\n".encode())
                resp = sock.recv(1024**2)

                # ratelimited / ip blocked
                if resp.startswith(b"HTTP/1.1 429") or resp.startswith(b"HTTP/1.1 403"):
                    raise Exception(
                        "Ratelimit or IP is blocked")
                # invalid group
                if resp.startswith(b"HTTP/1.1 400"):
                    gid_ignore[gid] = True
                    local_counter.count()
                    continue
                # server error
                if resp.startswith(b"HTTP/1.1 500"):
                    raise Exception(
                        "Server returned internal error")
                # unexpected status
                if not resp.startswith(b"HTTP/1.1 200"):
                    raise Exception(
                        f"Unrecognized statusline while reading response: {resp[:20]}")
                
                data = json.loads(resp.split(b"\r\n\r\n", 1)[1])
                local_counter.count()

                # skip and ignore locked groups
                if data.get("isLocked"):
                    gid_ignore[gid] = True
                    continue
                # skip and ignore no owner & no public entry groups
                if not data.get("owner") and not data.get("publicEntryAllowed"):
                    gid_ignore[gid] = True
                    continue
                # skip unclaimable groups
                if data.get("owner") or not data.get("publicEntryAllowed"):
                    continue
                # skip groups with less members than specified
                if min_members and min_members > data["memberCount"]:
                    continue
                
                # get group funds
                funds = None
                for _ in range(3):
                    try:
                        funds = get_group_funds(
                            gid,
                            proxy_addr=proxies and next(proxies),
                            timeout=timeout)
                        break
                    except:
                        pass

                # skip groups with less funds than specified
                if min_funds and (not funds or min_funds > funds):
                    continue

                # avoid notifying user about the same group multiple times
                gid_ignore[gid] = True
                
                # log group info to console (id - name - members - funds)
                print(f"\rFound group: {data['id']} - {data['name']} - {data['memberCount']} - {f'{funds} R$' if funds is not None else '?'}" + (" " * 30), end="\n")
                
                if webhook_url:
                    # send group details to webhook
                    send_webhook(webhook_url, embeds=[embed_from_group(data, funds)])

            except Exception as err:
                logging.warning(f"Dropping connection due to error: {err!r}")
                retry_gid = gid
                break
    
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()
        