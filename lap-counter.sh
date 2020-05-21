#!/bin/bash
BACKYARD_PATH=/usr/local/bin/backyard
CONF=$BACKYARD_PATH/lap-counter/lap-counter.conf
docker-compose -f $BACKYARD_PATH/lap-counter/docker-compose.yml down > /dev/null 2>&1 || true
docker-compose -f $BACKYARD_PATH/lap-counter/docker-compose.yml up -d
if [[ -f $CONF ]]; then
	source $CONF
	if [[ $VIEW == "true" || $VIEW == "yes" ]]; then
		VIEW="--view"
	fi
	if [[ $CAPTURE == "true" || $CAPTURE == "yes" ]]; then
		CAPTURE="--capture"
	fi
fi
python3 $BACKYARD_PATH/lap-counter/LapCounterByCamCV.py $VIEW $CAPTURE --sensitivity ${SENSITIVITY:-"200"} --lap-length ${LAP_LENGTH:-"33"} > /tmp/laps-counter.log 2>&1
