# roblox-group-scanner
Python 3 tool for finding unclaimed groups on Roblox, with support for multi-threading, multi-processing and HTTP proxies.

# Usage
```
usage: scanner [-h] [-t THREADS] [-w WORKERS] [-r RANGE] [-p PROXY_LIST] [-u WEBHOOK_URL]

optional arguments:
  -h, --help            show this help message and exit
  -t THREADS, --threads THREADS
                        Number of threads per worker
  -w WORKERS, --workers WORKERS
                        Number of workers
  -r RANGE, --range RANGE
                        Group id range
  -p PROXY_LIST, --proxy-list PROXY_LIST
                        File containg list of proxies
  -u WEBHOOK_URL, --webhook-url WEBHOOK_URL
                        URL of webhook to be called when a claimable group is found
```

```bash
python scanner --proxy-list proxies.txt --workers 16 --threads 500 --range 1-11000000
```
