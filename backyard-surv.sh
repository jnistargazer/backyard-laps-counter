#!/bin/bash
set -e -u -o pipefail

CONF=$(dirname $0)/backyard-surv.conf

conf=$(python3 << PY
import json
with open("$CONF") as fp:
   conf = json.load(fp)
   print('SENSITIVITY={}\nSHOW={}\nOUTPUT={}'.format(conf.get('sensitivity',50),
           conf.get('show','false'), conf.get('output','./')))
PY
)
echo "$conf"
eval "$conf"
# This is a hack. Should be removed if the lib can be found automatically
LD_PRELOAD=${LD_PRELOAD:-""}
export LD_PRELOAD=$LD_PRELOAD:/usr/lib/arm-linux-gnueabihf/libatomic.so.1
export DISPLAY=${1:-"localhost:0.0"}
python3 ./backyard-surv.py --show $SHOW --sensitivity $SENSITIVITY --output $OUTPUT
