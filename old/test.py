#!/usr/bin/env python
import sys, asyncio, time
import websockets
from websockets import WebSocketServerProtocol
 
async def consumer(msg):
    with open("/tmp/consumer.log","w+") as fp:
        fp.write(msg)
    print(msg)

async def consumer_handler(wsock, path):
    print("Consumer waiting for msg ...")
    while True:
        async for msg in wsock:
            await consumer(msg)

cnt = 0
async def producer():
    global cnt
    await asyncio.sleep(15)
    cnt += 1
    if cnt % 5 == 0:
        return "{} Hello".format(cnt)
    else:
        return ""

async def producer_handler(wsock, path):
    while True:
        msg = await producer()
        #print("send {}".format(str(msg)))
        if msg:
            await wsock.send(str(msg))

async def handler(wsock, path):
    producers = asyncio.ensure_future(producer_handler(wsock, path))
    consumers = asyncio.ensure_future(consumer_handler(wsock, path))
    done, pending = await asyncio.wait([consumers],
                                     return_when=asyncio.ALL_COMPLETED,
                                    )
    for task in pending:
        task.cacnel()

start_server = websockets.serve(handler, "0.0.0.0", 5678)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
