#!/usr/bin/env python3
import sys
#from gpiozero import LED
from threading import Thread
from threading import _active as active_threads
import pygame, time, ctypes
import time, signal
import asyncio
import datetime
import random
import websockets
from websockets import WebSocketServerProtocol
import CamMotion
 
LED_PIN = 17
Start = False 
KeepRunning = True
Laps = -1
clients = set()

class CheerLeader(Thread):
    def __init__(self):
        super().__init__()
        pygame.init()
        self.sound = pygame.mixer.Sound("/home/pi/workspace/laps-counter/Cheer.wav")
        self.sound.set_volume(100)
    def run(self):
        global Laps, KeepRunning
        cheered = False
        while KeepRunning:
            if Laps > 0 and Laps % 10 == 0:
                if not cheered:
                    self.sound.play()
                    cheered = True
            else:
                cheered = False
                time.sleep(1.0)

class LapCounter(Thread):
    def __init__(self):
        super().__init__()
        #self.led = LED(LED_PIN)
        #self.led.off()
        self.last_time = None
        self.camera = None
    def run(self):
        global Laps, KeepRunning
        self.camera = CamMotion.start_camera(self, nvecs=10, motion_threshold=50)
        while KeepRunning:
            self.camera.wait_recording(1)
        self.camera.stop_recording()
        self.camera.close()
        print("Ok, camera stops after {} motion events detected".format(Laps))

    def handle_motion(self,motion):
        global Start, Laps

        if motion:
           #self.led.on()
           now = time.time()
           if Start:
               if not self.last_time or now - self.last_time > 5.0:
                   self.camera.capture("capture/cap{}.jpg".format(Laps))
                   Laps += 1
           self.last_time = now
        else:
           #self.led.off()
           pass
    def start_counting(self):
        global Start
        Start = True
        self.last_time = None
    def stop_counting(self):
        global Start
        Start = False
        self.last_time = None
    def reset_counter(self):
        global Laps
        Laps = 0
 

async def register(wsock):
    global clients, Laps
    #print("A new client registered: {}".format((wsock,Laps)))
    clients.add((wsock,Laps))

async def unregister(client):
    global clients
    #print("A client unregistered: {}".format(client))
    clients.remove(client)

async def get_laps():
    global Start, Laps
    if Start:
        return Laps
    else:
        return None

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
    global KeepRunning
    while KeepRunning:
        laps = await get_laps()
        if laps is not None:
            #print("producer_handler({},{})".format(wsock, path))
            await asyncio.wait([update_client(client, laps) for client in clients])
        else:
            await asyncio.sleep(0.5)


async def commander(cmd):
    global Laps, counter, KeepRunning
    print(cmd)
    if cmd == "start":
       counter.start_counting()
    elif cmd == "stop":
       counter.stop_counting()
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

my_threads = []
counter = LapsCounter()
counter.start()
my_threads.append(counter)
cheer = CheerLeader()
cheer.start()
my_threads.append(cheer)

old_signal_handler = signal.getsignal(signal.SIGINT)
def exit_cleanup(sig, tmp):
    counter.led.off()
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

signal.signal(signal.SIGINT, exit_cleanup)

start_server = websockets.serve(handler, "0.0.0.0", 5678)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()

counter.join()
cheer.join()
