from easyrequests import (Methods, Queue)
import time

def callback(resp):
    print(f"Response received for: {resp.url}")

def parallel_background():
    queue = Queue()

    queue.add("https://twitter.com/", callback)
    queue.add("https://facebook.com/", callback)
    queue.add("https://google.com/", callback)
    queue.add("https://aol.com/", callback)
    queue.add("https://gmail.com/", callback)

    print("Dispatching Queue in Parallel (Background)...")

    queue.runparallel(clear=True, background=True)

    # if we dont wait, the interpreter will exit before all responses arrived.
    queue.waitforfinish()

def parallel_foreground():
    queue = Queue()

    queue.add("https://twitter.com/", callback)
    queue.add("https://facebook.com/", callback)
    queue.add("https://google.com/", callback)
    queue.add("https://aol.com/", callback)
    queue.add("https://gmail.com/", callback)

    print("Dispatching Queue in Parallel (Foreground)...")

    queue.runparallel(clear=True, background=False)

parallel_foreground()
parallel_background()

print("Done.")