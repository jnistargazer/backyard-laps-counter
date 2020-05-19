#!/usr/bin/env python3
import sys
from threading import Thread
from threading import _active as active_threads
import pygame, time, ctypes
import time, signal
import asyncio
import datetime
import random
import websockets
from websockets import WebSocketServerProtocol
import CamMotionCV
 
Start = False 
KeepRunning = True
clients = set()
Laps = -1
class CheerLeader(Thread):
    def __init__(self):
        super().__init__()
        pygame.init()
        self.sound = pygame.mixer.Sound("/home/pi/workspace/laps-counter/Cheer.wav")
        self.sound.set_volume(100)
    def run(self):
        global KeepRunning, Laps
        cheered = False
        while KeepRunning:
            #laps = self.counter.get_laps()
            if Laps > 0 and Laps % 10 == 0:
                if not cheered:
                    self.sound.play()
                    cheered = True
            else:
                cheered = False
                time.sleep(1.0)

class LapCounter(Thread):
    def __init__(self, show=False, capture=False):
        super().__init__()
        self.camera = None
        self.show = show
        self.capture = capture
        self.then = None
        #self.laps = -1
    def run(self):
        self.camera = CamMotionCV.MotionDetector(src="picam",show=self.show, capture=self.capture)
        self.camera.detect_motion(self)
    def handle_motion(self,motion):
        global Start, Laps
        #print("Motion detected")
        if not Start:
            return None
        #print("Counting started")
        if motion:
           now = time.time()
           if not self.then:
               elapsed = 0
               self.then = now
           else:
               elapsed = now - self.then
           if elapsed > 5:
               self.then = now
               #self.laps += 1
               Laps += 1
               print("Lap #{}".format(Laps))
               return Laps
        else:
           pass
        return None

    def start_counting(self):
        global Start
        Start = True
        self.last_time = None
    def stop_counting(self):
        global Start
        Start = False
        self.last_time = None
    def finish(self):
        pass
    def reset_counter(self):
        #self.laps = 0
        Laps = 0
 

async def register(wsock):
    global clients, Laps, LapLength
    laps = Laps
    clients.add((wsock,laps))
    try:
        await wsock.send("lap-length={}".format(LapLength))
    except Exception as e:
        #print(str(e))
        print("Register: Client {} seems gone".format(client))
        await unregister((wsock,laps))

async def unregister(client):
    global clients
    clients.remove(client)

async def update_client(client, laps):
      try:
          wsock, L = client
          if L:
              L = laps - L
              await wsock.send(str(L))
      except Exception as e:
          #print(str(e))
          print("Client {} seems gone".format(client))
          await unregister(client)

async def producer_handler(wsock, path):
    global KeepRunning, Start
    while KeepRunning:
        if Start:
            await asyncio.wait([update_client(client, Laps) for client in clients])
        else:
            await asyncio.sleep(0.5)


async def commander(cmd):
    global counter, KeepRunning
    print(cmd)
    if cmd == "start":
       counter.start_counting()
    elif cmd == "stop":
       counter.stop_counting()
    elif cmd == "finish":
       counter.finish()
    elif cmd == "reset":
       counter.reset_counter()
    elif cmd == "exit":
       KeepRunning = False
    
async def consumer_handler(wsock, path):
    global KeepRunning
    try:
        while KeepRunning:
            async for msg in wsock:
                await commander(msg)
    except:
        pass

async def handler(wsock, path):
    await register(wsock)
    consumer = asyncio.ensure_future(
        consumer_handler(wsock, path)
    ) 
    producer = asyncio.ensure_future(
        producer_handler(wsock, path)
    ) 

    done, pending = await asyncio.wait(
        [consumer, producer],
        return_when=asyncio.ALL_COMPLETED,
    )
    for task in pending:
        task.cancel()

def exit_cleanup(sig, tmp):
    print("exiting ... cleanning up ...")
    signal.signal(signal.SIGINT, old_signal_handler)
    thrds = active_threads.items()
    for id, thrd in thrds:
        if thrd in my_threads:
            try:
                r = ctypes.pythonapi.PyThreadState_SetAsyncExc(id,ctypes.py_object(SystemExit))
                if r > 1:
                    print('Failed to stop sensor')
                    sys.exit(1)
                else:
                    thrd.join()
            except:
                continue
    sys.exit(0)

if __name__ == "__main__":
    show = False
    capture = False
    # My backyard!! In meters
    LapLength = 33
    nargs = len(sys.argv)
    if nargs > 1:
        opt = sys.argv[1]
        if opt in ["--show", "--capture", "--lap-length"]:
            if opt == "--show":
                show = True
            elif opt == "--capture":
                capture = True
            elif opt == "--lap-length":
                if nargs > 2:
                    LapLength = int(sys.argv[2])
                else:
                    print("Usage: {} [--show] [--capture] [--lap-length <number>]".format(sys.argv[0]))
                    sys.exit(1)


    my_threads = []
    counter = LapCounter(show=show, capture=capture)
    counter.start()
    my_threads.append(counter)
    #cheer = CheerLeader()
    #cheer.start()
    #my_threads.append(cheer)

    old_signal_handler = signal.getsignal(signal.SIGINT)

    signal.signal(signal.SIGINT, exit_cleanup)

    start_server = websockets.serve(handler, "0.0.0.0", 5678)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()

    counter.join()
    #cheer.join()
