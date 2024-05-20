#!/bin/bash

pid_file=".draft/pids/helper_sidecar.pid"
# Check if pid file exists
if [ -f "$pid_file" ]; then
    echo "Error: $pid_file already exists."
    exit 1
fi

config_path=$1
root_path=$2
root_domain=$3
helper_domain=$4
sidecar_domain=$5
helper_port=$6
sidecar_port=$7
identity=$8

nohup draft run-helper-sidecar --config_path "$config_path" --root_path "$root_path" --root_domain "$root_domain" --helper_domain "$helper_domain" --sidecar_domain "$sidecar_domain" --helper_port "$helper_port" --sidecar_port "$sidecar_port" --identity "$identity" > .draft/logs/helper_sidecar.log 2>&1 & echo $! > $pid_file
