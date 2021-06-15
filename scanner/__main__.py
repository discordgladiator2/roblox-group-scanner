from arguments import parse_args
from workers import worker_func
import multiprocessing
import random
import time

args = parse_args()
proxies = None

# load proxies if specified
if args.proxy_list:
    proxies = args.proxy_list.read().splitlines()
    proxies = [(x.split(":")[0], int(x.split(":")[1]))
               for x in proxies]
    args.proxy_list.close()

# create workers
gid_per_worker = int((args.range[1] - args.range[0]) / args.workers)
proxies_per_worker = proxies and int(len(proxies)/args.workers)
worker_barrier = multiprocessing.Barrier(args.workers + 1)
count_queue = multiprocessing.Queue()
workers = []

for worker_num in range(args.workers):
    # split id range for this worker
    gid_range = (
        args.range[0] + (gid_per_worker * worker_num),
        args.range[0] + (gid_per_worker * (worker_num + 1)),
    )

    # split proxies for this worker
    proxy_chunk = None
    if proxies:
        proxy_chunk = proxies[proxies_per_worker * worker_num:proxies_per_worker * (worker_num+1)]
        random.shuffle(proxy_chunk)

    # create worker
    worker = multiprocessing.Process(
        target=worker_func,
        args=(worker_num, worker_barrier, args.threads,
              args.webhook_url,
              count_queue, gid_range, proxy_chunk,
              args.min_funds, args.min_members,
              args.timeout)
    )
    workers.append(worker)

# delete unused variables
del worker
del proxies

# start workers
for worker in workers:
    worker.start()
worker_barrier.wait()

# count checks per minute
count_cache = []
while any(w.is_alive() for w in workers):
    count_cache.append((time.time(), count_queue.get()))
    count_cache = [x for x in count_cache if 60 > time.time() - x[0]]
    cpm = sum([x[1] for x in count_cache])
    print(f"\rCPM: {cpm}", end="")