#!/usr/bin/env python3
import sys
from gpiozero import LED
from gpiozero import MotionSensor
from threading import Thread
from threading import _active as active_threads
import pygame, time, ctypes
import time, signal
import asyncio
import datetime
import random
import websockets
from websockets import WebSocketServerProtocol
 
MOTION_SENSOR_PIN = 4
LED_PIN = 17
Start = False 
MotionSensed = False
Laps = -1
clients = set()

class CheerLeader(Thread):
    def __init__(self):
        super().__init__()
        pygame.init()
        self.sound = pygame.mixer.Sound("/home/pi/workspace/laps-counter/Cheer.wav")
        self.sound.set_volume(100)
    def run(self):
        global Laps
        cheered = False
        while True:
            if Laps > 0 and Laps % 10 == 0:
                if not cheered:
                    self.sound.play()
                    cheered = True
            else:
                cheered = False
                time.sleep(1.0)

class MotionDetector(Thread):
    def __init__(self):
        super().__init__()
        self.led = LED(LED_PIN)
        self.sensor = MotionSensor(MOTION_SENSOR_PIN)
        self.led.off()
    def run(self):
        self.start_counting()

    def start_counting(self):
        global Start, Laps, MotionSensed
        while True: 
            self.sensor.wait_for_motion()
            if Start:
                #print("Montion detected and counted!")
                Laps += 1
                MotionSensed = True
            #else:
                #print("Montion detected but not counted")
            self.led.on()
            self.sensor.wait_for_no_motion() 
            self.led.off()
    def stop_counting(self):
         Start = False
 

async def register(wsock):
    global clients, Laps
    #print("A new client registered: {}".format((wsock,Laps)))
    clients.add((wsock,Laps))

async def unregister(client):
    global clients
    #print("A client unregistered: {}".format(client))
    clients.remove(client)

async def get_laps():
    global Start, MotionSensed, Laps
    if Start and MotionSensed:
        MotionSensed = False
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
          #print("Client {} seems gone".format(client))
          await unregister(client)

async def producer_handler(wsock, path):
    while True:
        laps = await get_laps()
        if laps is not None:
            #print("producer_handler({},{})".format(wsock, path))
            await asyncio.wait([update_client(client, laps) for client in clients])
        else:
            await asyncio.sleep(0.5)


async def commander(cmd):
    global Laps, Start
    print(cmd)
    if cmd == "start":
       Start = True
    elif cmd == "stop":
       Start = False
    elif cmd == "reset":
       Laps = 0
    
async def consumer_handler(wsock, path):
    while True:
        async for msg in wsock:
            await commander(msg)

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

counter = MotionDetector()
counter.start()

#cheer = CheerLeader()
#cheer.start()

old_signal_handler = signal.getsignal(signal.SIGINT)
def exit_cleanup(sig, tmp):
    counter.led.off()
    signal.signal(signal.SIGINT, old_signal_handler)
    thrds = active_threads.items()
    for id, thrd in thrds:
        if thrd in [counter, cheer]:
            r = ctypes.pythonapi.PyThreadState_SetAsyncExc(id,ctypes.py_object(SystemExit))
            if r > 1:
                print('Failed to stop sensor')
                sys.exit(1)
            else:
                thrd.join()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_cleanup)

start_server = websockets.serve(handler, "0.0.0.0", 5678)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()

counter.join()
#cheer.join()
