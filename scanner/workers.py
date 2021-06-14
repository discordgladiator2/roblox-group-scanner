from scanners import scanner_func
from structures import LocalCounter
import multiprocessing
import threading
import itertools
import os
if os.name == "nt":
    import win32process

def worker_func(worker_num, worker_barrier, thread_count,
                webhook_url, count_queue, gid_range, proxies):
    # set cpu affinity for this process
    cpu_num = worker_num % multiprocessing.cpu_count()
    if os.name == "nt":
        win32process.SetProcessAffinityMask(-1, 1 << cpu_num)
    else:
        os.sched_setaffinity(0, [cpu_num])

    # start threads
    gid_counter = itertools.count(0)
    gid_lock = threading.Lock()
    gid_cache = {}
    local_counter = LocalCounter(notify_per=1000)
    proxies = proxies and itertools.cycle(proxies) or None
    thread_barrier = threading.Barrier(thread_count + 1)
    thread_event = threading.Event()

    threads = [
        threading.Thread(
            target=scanner_func,
            args=(worker_num, thread_num, thread_barrier, thread_event,
                  gid_counter, gid_range, gid_lock, gid_cache,
                  webhook_url,
                  local_counter, proxies)
        )
        for thread_num in range(thread_count)
    ]

    for thread in threads:
        thread.start()
    # wait for threads to initialize
    thread_barrier.wait()
    # wait for other workers
    worker_barrier.wait()
    # notify threads
    thread_event.set()
    
    # pass counts to main process
    while any(t.is_alive() for t in threads):
        count_queue.put(local_counter.wait())