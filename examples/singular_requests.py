from easyrequests import (Methods, Queue)
import time

def callback(resp):
    print(f"Response received for: {resp.url}")

# If ran with background set to 'false' the interpreter will be blocked until the request has completed.
def foreground():
    print("Requesting Facebook.com (Background = False)")
    Queue.single("https://facebook.com/",
                callback,
                method=Methods.GET,
                timeout=10,
                background=False)

# If background is set to 'true' the request will be executed in a seperate thread.
def background():
    print("Requesting Google.com (Background = True)")
    Queue.single("https://google.com/",
                callback,
                method=Methods.GET,
                timeout=10,
                background=True)

background()
foreground()

time.sleep(5)