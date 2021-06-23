from scanners import scanner_func
from structures import ChunkCounter
import multiprocessing
import threading
import itertools
import os
if os.name == "nt":
    from win import set_affinity

def worker_func(worker_num, worker_barrier, thread_count,
                count_queue,
                webhook_url,
                proxies, timeout, no_close,
                gid_range, gid_cutoff,
                min_funds, min_members):
    # set cpu affinity for this process
    cpu_num = worker_num % multiprocessing.cpu_count()
    if os.name == "nt":
        set_affinity(0, 1 << cpu_num)
    else:
        os.sched_setaffinity(0, [cpu_num])

    proxies = proxies and itertools.cycle(proxies) or None
    local_counter = ChunkCounter(notify_per=1000)
    gid_counter = itertools.count(0)
    gid_ignore = {}

    # create & start threads
    thread_barrier = threading.Barrier(thread_count + 1)
    thread_event = threading.Event()
    threads = [
        threading.Thread(
            target=scanner_func,
            kwargs=dict(
                worker_num=worker_num,
                thread_num=thread_num,
                thread_barrier=thread_barrier,
                thread_event=thread_event,
                webhook_url=webhook_url,
                proxies=proxies,
                timeout=timeout,
                no_close=no_close,
                local_counter=local_counter,
                gid_counter=gid_counter,
                gid_range=gid_range,
                gid_ignore=gid_ignore,
                gid_cutoff=gid_cutoff,
                min_funds=min_funds,
                min_members=min_members
            )
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