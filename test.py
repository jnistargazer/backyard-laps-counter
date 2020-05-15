#!/usr/bin/env python3
import sys
import time
import asyncio

async def my_sleep(t:int):
    time.sleep(t)


async def do_it():
    print("1")
    await asyncio.sleep(1)
    print("2")


async def run():
    await asyncio.gather(do_it(), do_it(), do_it())

if __name__ == "__main__":
    asyncio.run(run())
