import asyncio
from dataclasses import dataclass
from distutils.log import debug
import aiohttp
from datetime import datetime, timedelta
from enum import Enum
import platform
from functools import wraps

class Methods(Enum):
    GET = 1
    POST = 2
    PUT = 3
    DELETE = 4
    PATCH = 5
    OPTIONS = 6
    HEAD = 7

@dataclass
class CallbackResponse():
    url: any
    method: any
    headers: any
    content: any

# Windows related error (https://lifesaver.codes/answer/runtimeerror-event-loop-is-closed-when-proactoreventloop-is-used-4324)
if platform.system() == 'Windows':
    from asyncio.proactor_events import _ProactorBasePipeTransport
    def silence_event_loop_closed(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise
        return wrapper
    _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)

class Queue():
    def __init__(self) -> None:
        self._queue = []
        self._idCounter = 1
        self._loading = False

    def getqueue(self):
        self._queue = self._queue or []
        return self._queue

    def isloading(self):
        return self._loading

    def waitforfinish(self, timeout:float=None):
        end = datetime.now() + timedelta(seconds=timeout or 0)
        while self._loading == True:
            if timeout and (end - datetime.now()).total_seconds() <= 0:
                break

    def __add(self, index, url, callback, method=Methods.GET, timeout=15, **kwargs) -> bool:
        if not url: return False
        if not method: return False
        if not callback: return False

        timeout = timeout or 15

        temp = {
            "id": self._idCounter,
            "url": url,
            "method": method,
            "timeout": timeout,
            "callback": callback
        }

        if kwargs: temp["kwargs"] = {k: v for (k, v) in kwargs.items()}

        self._queue.insert(index, temp)
        self._idCounter += 1

        return True

    def add(self, url, callback, method=Methods.GET, timeout=15, **kwargs) -> bool:
        return self.__add(len(self._queue), url, callback, method, timeout, **kwargs)

    def remove(self, url) -> bool:
        if not url: return False
        result = []
        for item in self._queue:
            if "url" in item: continue
            if url == item["url"]: continue
            result.append(item)
        self._queue = result
        return True

    def insert(self, index, url, callback, method=Methods.GET, timeout=15, **kwargs) -> bool:
        if index < 0: return False
        return self.__add(index, url, callback, method, timeout, **kwargs)

    async def __doRequest(self, session: aiohttp.ClientSession, item):
        if not item or not session: return

        try:
            payload = {}
            allow_redirects = True

            if "kwargs" in item:
                payload = item["kwargs"]["data"] if ("data" in item["kwargs"]) else {}
                allow_redirects = item["kwargs"]["allow_redirects"] if ("allow_redirects" in item["kwargs"]) else True

            async def cb(response):
                item["callback"](CallbackResponse(item["url"],
                                        response.method,
                                        {k:v for (k,v) in response.headers.items()},
                                        await response.read()))

            # GET
            if item["method"] == Methods.GET:
                async with session.get(item["url"], allow_redirects=allow_redirects) as response:
                    await cb(response)
            # POST
            elif item["method"] == Methods.POST:
                async with session.post(item["url"], data=payload) as response:
                    await cb(response)
            # PATCH
            elif item["method"] == Methods.PATCH:
                async with session.patch(item["url"], data=payload) as response:
                    await cb(response)
            # DELETE
            elif item["method"] == Methods.DELETE:
                async with session.delete(item["url"]) as response:
                    await cb(response)
            # OPTIONS
            elif item["method"] == Methods.OPTIONS:
                async with session.options(item["url"], allow_redirects=allow_redirects) as response:
                    await cb(response)
            # PUT
            elif item["method"] == Methods.PUT:
                async with session.put(item["url"], data=payload) as response:
                    await cb(response)
            # HEAD
            elif item["method"] == Methods.HEAD:
                async with session.head(item["url"], allow_redirects=allow_redirects) as response:
                    await cb(response)

        except Exception as e:
            if str(e) ==  'Event loop is closed': return
            print(f"Error: {e}")

    @classmethod
    def single(self, url, callback, method=Methods.GET, timeout=15, background=True, **kwargs):
        async def __request(item):
            async with aiohttp.ClientSession() as session:
                await self.__doRequest(self, session, item)

        temp = {
            "url": url,
            "method": method,
            "timeout": timeout,
            "callback": callback
        }

        if kwargs: temp["kwargs"] = {k: v for (k, v) in kwargs.items()}

        def exec():
            try:
                asyncio.run(__request(item=temp), debug=True)
            except Exception as e:
                if str(e) ==  'Event loop is closed': return
                print(f"Error: {e}")

        if background:
            import threading
            t = threading.Thread(target=exec)
            t.start()
        else:
            exec()

    def __execute(self, loop, worker, *args):
        try:
            loop.run_until_complete(worker(*args))
        except Exception as e:
            if isinstance(e, RuntimeWarning): return
            if isinstance(e, RuntimeError) and str(e) == 'Event loop is closed': return
            print(f"Error: {e}")
       # loop.run_until_complete(asyncio.sleep(1)) # bug -> https://github.com/encode/httpx/issues/914#issuecomment-780023632
        loop.close()

    async def __sequential(self, clear):
        async with aiohttp.ClientSession() as session:
            for item in self._queue:
                await self.__doRequest(session, item)
        if clear:
            self._queue = []

    def runsequential(self, clear=True, background=True):
        if self._loading == True: return

        self._loading = True
        eventLoop = asyncio.new_event_loop()

        def exec(loop):
            self.__execute(loop, self.__sequential, clear)
            self._loading = False

        if background:
            import threading
            t = threading.Thread(target=exec, args=(eventLoop,))
            t.start()
        else:
            exec(eventLoop)

    async def __parallel(self, clear):
        async with aiohttp.ClientSession() as session:
            result = await asyncio.gather(*[self.__doRequest(session, item) for item in self._queue])
        if clear:
            self._queue = []

    def runparallel(self, clear=True, background=True):
        if self._loading == True: return

        self._loading = True
        eventLoop = asyncio.new_event_loop()

        def exec(loop):
            self.__execute(loop, self.__parallel, clear)
            self._loading = False

        if background:
            import threading
            t = threading.Thread(target=exec, args=(eventLoop,))
            t.start()
        else:
            exec(eventLoop)
