#!/bin/bash
set -e -u -o pipefail
op=$1
PIDFILE=/var/birding/birding.pid
if [[ $op == "stop" ]]; then
    if [[ -f $PIDFILE ]]; then
        kill -9 $(cat $PIDFILE)
        rm -f $PIDFILE
        echo "bird-watcher killed"
    fi
    exit 0
fi
 
if [[ -f $PIDFILE ]]; then
   if ps -p $(cat $PIDFILE); then
	echo "bird-watcher is running"
        exit 0
   else
        echo "Stale PID file found. Removed."
        rm -f $PIDFILE
   fi
fi

MYPATH=$(dirname $0)
CONF=$MYPATH/bird-watcher.conf

conf=$(python3 << PY
import json
with open("$CONF") as fp:
   conf = json.load(fp)
   print('SENSITIVITY={}\nRECORD_LEN={}\nSHOW={}\nOUTPUT={}'.format(conf.get('sensitivity',50),conf.get('record-length',5),
           conf.get('show','false'), conf.get('output','./')))
PY
)
echo "$conf"
eval "$conf"
# This is a hack. Should be removed if the lib can be found automatically
LD_PRELOAD=${LD_PRELOAD:-""}
export LD_PRELOAD=$LD_PRELOAD:/usr/lib/arm-linux-gnueabihf/libatomic.so.1
export DISPLAY=${1:-"localhost:0.0"}
python3 $MYPATH/bird-watcher.py --show $SHOW --sensitivity $SENSITIVITY --output $OUTPUT --record-length=$RECORD_LEN &
echo $! > $PIDFILE
echo "PID file = $PIDFILE"
echo "CONF file = $CONF"
while true; do
   sleep 60
done
