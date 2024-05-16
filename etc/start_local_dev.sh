#!/bin/bash

pid_file=".draft/pids/local_dev.pid"
# Check if pid file exists
if [ -f "$pid_file" ]; then
    echo "Error: $pid_file already exists."
    exit 1
fi

config_path=$1
root_path=$2
helper_start_port=$3
sidecar_start_port=$4

nohup draft run-local-dev --config_path "$config_path" --root_path "$root_path" --helper_start_port "$helper_start_port" --sidecar_start_port "$sidecar_start_port" > .draft/logs/local_dev.log 2>&1 & echo $! > $pid_file
