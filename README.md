# EasyRequests

EasyRequests is a minimalistic HTTP-Request Library that wraps aiohttp and asyncio in a small package that allows for sequential, parallel or even single requests. EasyRequests also supports dispatching each request as daemon (*in a seperate thread*)

## Installation

Download the `.py` file and place it in your project.
As of writing this, there is currently **no PyPi download** available!

## Usage

### Example usage
```python
from easyrequests import  (Methods, Queue)

def callback(resp):
	print(f"Response received for: {resp.url}")

queue = Queue()

# A bunch of GET Requests
queue.add("https://twitter.com/", callback)
queue.add("https://facebook.com/", callback)
queue.add("https://google.com/", callback)
queue.add("https://aol.com/", callback)
queue.add("https://gmail.com/", callback)

# You can also specify the Method, in this case "POST"
queue.add("https://discord.com",
		  method=Methods.POST,
	      timeout=60,
	      data={"Hello":  "World"})

# clear -> After finishing, clear the queue
# background -> run as daemon or not
queue.runparallel(clear=True, background=True)

# If we don't do this, an exception will be thrown if the interpreter reaches the end of the file!
# We only need to use this if the task is run as daemon
queue.waitforfinish()
```
We can also do `sequential` requests by using the function `runsequential()` instead of `runparallel()`.

EasyRequests also supports making single requests, without using a queue.
```python
from easyrequests import  (Methods, Queue)

def callback(resp):
	print(f"Response received for: {resp.url}")

Queue.single("https://google.com/",
			 callback,
			 method=Methods.GET,
			 timeout=10,
		     background=True)
```


## Please note

I created this library for **personal use**! If you encounter any problems, feel free to open an issue, though if I don't see the need to develop this further, I will abandon the project! **Use at your own risk!**