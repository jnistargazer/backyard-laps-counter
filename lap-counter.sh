#!/bin/bash
set -e -u -o pipefail
CONF=./lap-counter.conf
# This is a hack. Should be removed if the lib can be found automatically
LD_PRELOAD=${LD_PRELOAD:-""}
export LD_PRELOAD=$LD_PRELOAD:/usr/lib/arm-linux-gnueabihf/libatomic.so.1
python3 ./CamMotionCV.py
