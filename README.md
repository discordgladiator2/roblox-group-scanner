# roblox-group-scanner
Python 3 tool for finding unclaimed groups on Roblox. Supports multi-threading, multi-processing and HTTP proxies.

# Usage
```
usage: scanner [-h] [-t THREADS] [-w WORKERS] [-r RANGE] [--timeout TIMEOUT] [-p PROXY_LIST] [-u WEBHOOK_URL]
               [-f MIN_FUNDS] [-m MIN_MEMBERS] [-n] [-c CUT_OFF]

optional arguments:
  -h, --help            show this help message and exit
  -t THREADS, --threads THREADS
                        Number of threads per worker
  -w WORKERS, --workers WORKERS
                        Number of workers
  -r RANGE, --range RANGE
                        Group id range
  --timeout TIMEOUT     Max. time for connections and responses
  -p PROXY_LIST, --proxy-list PROXY_LIST
                        File containg list of proxies
  -u WEBHOOK_URL, --webhook-url WEBHOOK_URL
                        URL of webhook to be called when a claimable group is found
  -f MIN_FUNDS, --min-funds MIN_FUNDS
                        Min. amount of funds in a group
  -m MIN_MEMBERS, --min-members MIN_MEMBERS
                        Min. amount of members in a group
  -n, --no-close        If enabled, connections won't be closed based on responses. This is useful for proxies that
                        switch IPs per request.
  -c CUT_OFF, --cut-off CUT_OFF
                        Non-existent groups with IDs past this point won't be automatically skipped after the first
                        attempt
```

```bash
python scanner --proxy-list proxies.txt --workers 8 --threads 100 --range 1-11000000
```
