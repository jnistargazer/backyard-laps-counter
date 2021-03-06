#!/bin/bash
set -e -u -o pipefail
BACKYARD_PATH=/usr/local/bin/backyard
CONF=$BACKYARD_PATH/lap-counter/lap-counter.conf
docker-compose -f $BACKYARD_PATH/lap-counter/docker-compose.yml down > /dev/null 2>&1 || true
docker-compose -f $BACKYARD_PATH/lap-counter/docker-compose.yml up -d || true
VIEW=""
CAPTURE=""
source $CONF
if [[ $VIEW == "true" || $VIEW == "yes" ]]; then
		VIEW="--view"
fi
if [[ $CAPTURE == "true" || $CAPTURE == "yes" ]]; then
	CAPTURE="--capture"
fi
#python3 $BACKYARD_PATH/lap-counter/LapCounterByCamCV.py $VIEW $CAPTURE --sensitivity ${SENSITIVITY:-"200"} --lap-length ${LAP_LENGTH:-"33"} > /tmp/laps-counter.log 2>&1

# This is a hack. Should be removed if the lib can be found automatically
LD_PRELOAD=${LD_PRELOAD:-""}
export LD_PRELOAD=$LD_PRELOAD:/usr/lib/arm-linux-gnueabihf/libatomic.so.1
python3 $BACKYARD_PATH/lap-counter/LapCounterByCamCV.py $VIEW $CAPTURE --sensitivity ${SENSITIVITY:-"200"} --lap-length ${LAP_LENGTH:-"33"}
