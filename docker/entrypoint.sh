#!/bin/sh

SKIPIDENTICAL='--skipidentical 50' # Useful??

# NOTE:
#  I'm unsure why but the script appears to run for a while and then
#  just stops reporting, but doesn't stop executing, AND sometimes it
#  won't even report at the start and just sit idle. As a workaround
#  I'm limiting the number of reads (with --count), adding a timeout
#  and running it a loop
# TODO: Recheck if the timeout is still a requirement
TIMEOUT='2m'
SIGKILL_TIMEOUT='2m' # Extra time before a KILL signal is sent
MAX_READS_PER_ITERATION=10
SKIPIDENTICAL='--skipidentical 9'
PAUSE_BETWEEN_ITERATIONS='20s' # only if an iteration ends successfully

while : ; do
	date
	# Note the -u is important, without it the docker log appears empty
	timeout --foreground --kill-after=$SIGKILL_TIMEOUT $TIMEOUT \
		python3m -u /app/LYWSD03MMC.py \
		--passive \
 		--battery 100 \
		--count $MAX_READS_PER_ITERATION \
		$SKIPIDENTICAL \
		--onlydevicelist \
		--devicelistfile /conf/sensors.ini \
		--mqttconfigfile /conf/mqtt.conf
	if [ $? -ne 124 ]; then # did not time out
		sleep $PAUSE_BETWEEN_ITERATIONS
	fi
done >&2

