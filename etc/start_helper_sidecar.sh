#!/bin/bash

pid_file=".draft/pids/helper_sidecar.pid"
# Check if pid file exists
if [ -f "$pid_file" ]; then
    echo "Error: $pid_file already exists."
    exit 1
fi

config_path=$1
root_path=$2
helper_domain=$3
sidecar_domain=$4
helper_port=$5
sidecar_port=$6
identity=$7

log_file=".draft/logs/helper_sidecar_$(date "+%Y-%m-%d_%H-%M-%S").log"
nohup draft run-helper-sidecar --config_path "$config_path" --root_path "$root_path" --helper_domain "$helper_domain" --sidecar_domain "$sidecar_domain" --helper_port "$helper_port" --sidecar_port "$sidecar_port" --identity "$identity" > "$log_file" 2>&1 & echo $! > $pid_file
