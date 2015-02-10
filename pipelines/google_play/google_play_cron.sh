#!/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/bin/
export BOTO_CONFIG="/home/rrayborn/.boto"

python /home/shared/code/pipelines/google_play/google_play_manager.py >/tmp/google_play_cron 2>&1
