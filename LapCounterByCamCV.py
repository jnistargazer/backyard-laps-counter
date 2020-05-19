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
import argparse
 
Start = False 
LapUpdate = False 
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
    def __init__(self, show=False, capture=False, sensitivity=250):
        super().__init__()
        self.camera = None
        self.show = show
        self.capture = capture
        self.sensitivity = sensitivity
        self.then = None
        #self.laps = -1
    def run(self):
        self.camera = CamMotionCV.MotionDetector(src="picam",show=self.show, capture=self.capture, min_area=self.sensitivity)
        self.camera.detect_motion(self)
    def handle_motion(self,motion):
        global Start, Laps, LapUpdate
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
           if elapsed >= 5:
               self.then = now
               #self.laps += 1
               Laps += 1
               print("Lap #{}".format(Laps))
               LapUpdate = True
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
    global KeepRunning, LapUpdate
    while KeepRunning:
        if LapUpdate:
            LapUpdate = False
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
    aparser = argparse.ArgumentParser()
    aparser.add_argument("-v", "--view", nargs="?", const="yes", default="no", help="Show video")
    aparser.add_argument("-s", "--sensitivity", type=int, default=200, help="Motion detection sensitity (smaller number means more sensitive)")
    aparser.add_argument("-c", "--capture", nargs="?", const="yes", default="no", help="capture photos for each lap")
    aparser.add_argument("-l", "--lap-length", type=int, default=33, help="Length of a lap")
    args = vars(aparser.parse_args())
    print(args)
    if args.get("view", None) == "yes":
        show = True
    if args.get("capture", None) == "yes":
        capture = True
    if args.get("lap-length", None):
        LapLength = args.get("lap-length")
    if args.get("sensitivity", None):
        sensitivity = args.get("sensitivity")


    my_threads = []
    counter = LapCounter(show=show, capture=capture, sensitivity=sensitivity)
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
