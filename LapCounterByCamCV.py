#!/usr/bin/env python3
import sys, time, signal, datetime, random, ctypes, pygame, asyncio, argparse
import websockets, json
from threading import Thread
from threading import _active as active_threads
from websockets import WebSocketServerProtocol
import CamMotionCV
import subprocess
 
Start = False 
LapUpdate = False 
Elapsed = 0
KeepRunning = True
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
    def __init__(self, show=False, sensitivity=250):
        super().__init__()
        self.motion_sensor = None
        self.show = show
        self.sensitivity = sensitivity
        self.then = None
        #self.laps = -1
    def capture(self, flag):
        if self.motion_sensor:
           self.motion_sensor.set_capture(flag);
    def run(self):
        self.motion_sensor = CamMotionCV.MotionDetector(src="picam",show=self.show, min_area=self.sensitivity)
        self.motion_sensor.detect_motion(self)
    def handle_motion(self,motion):
        global Start, Laps, LapUpdate, Elapsed
        #print("Motion detected")
        if not Start:
            return None
        if motion:
           now = time.time()
           if not self.then:
               Laps = 0
               delta = 0
               self.T0 = now
               self.then = now
               # First motion detected
               LapUpdate = True
               print("Lap #{}".format(Laps))
           else:
               delta = now - self.then
           if delta >= 5:
               Elapsed = now - self.T0
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
        global Laps
        Laps = 0
 

clients = {}
async def register(wsock):
    global clients, LapLength, Elapsed
    client_ip = wsock.remote_address[0]
    print("Register: new client {}".format(client_ip))
    client = clients.get(client_ip, None)
    clients[client_ip] = wsock
    try:
        msg = {
            "lap": {
                "length":LapLength,
                "number":Laps,
                "time": Elapsed
            }
        }
        await wsock.send(json.dumps(msg))
    except Exception as e:
        #print(str(e))
        await unregister(wsock)

async def unregister(wsock):
    global clients
    client_ip = wsock.remote_address[0]
    print("Unregister: client {}".format(client_ip))
    if client_ip in clients:
        del clients[client_ip]
    print(clients)

async def update_client(wsock, lap_len, laps, elapsed):
      try:
          msg = {
            "lap": {
                "length":lap_len,
                "number":laps,
                "time": elapsed
            }
          }
          #print("Updating client:{}".format(msg))
          await wsock.send(json.dumps(msg))
          #print("Updated client:{}".format(msg))
      except Exception as e:
          print(str(e))
          print("Client {} seems gone".format(wsock))
          await unregister(wsock)

async def producer_handler(wsock, path):
    global KeepRunning, LapUpdate, Laps, LapLength, Elapsed
    while KeepRunning:
        if LapUpdate:
            LapUpdate = False
            try:
                await asyncio.wait([update_client(clients[client_ip], LapLength, Laps, Elapsed) for client_ip in clients])
            except:
                pass
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
    elif cmd == "capture":
       counter.capture(True)
    elif cmd == "no-capture":
       counter.capture(False)
    elif cmd == "shutdown":
       subprocess.call(['sudo', 'shutdown', 'now'])
    
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
    # My backyard!! In meters
    LapLength = 33
    aparser = argparse.ArgumentParser()
    aparser.add_argument("-v", "--view", nargs="?", const="yes", default="no", help="Show video")
    aparser.add_argument("-s", "--sensitivity", type=int, default=200, help="Motion detection sensitity (smaller number means more sensitive)")
    aparser.add_argument("-l", "--lap-length", type=int, default=33, help="Length of a lap")
    args = vars(aparser.parse_args())
    print(args)
    if args.get("view", None) == "yes":
        show = True
    if args.get("lap-length", None):
        LapLength = args.get("lap-length")
    if args.get("sensitivity", None):
        sensitivity = args.get("sensitivity")


    my_threads = []
    counter = LapCounter(show=show, sensitivity=sensitivity)
    counter.start()
    my_threads.append(counter)
    #cheer = CheerLeader()
    #cheer.start()
    #my_threads.append(cheer)

    old_signal_handler = signal.getsignal(signal.SIGINT)

    signal.signal(signal.SIGINT, exit_cleanup)

    start_server = websockets.serve(handler, "0.0.0.0", 5678)
    print("Server {}:".format(start_server))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()

    counter.join()
    #cheer.join()
