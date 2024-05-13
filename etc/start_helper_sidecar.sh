#!/bin/bash

config_path=$1
root_path=$2
root_domain=$3
sidecar_domain=$4
helper_port=$5
sidecar_port=$6
identity=$7

nohup draft run-helper-sidecar --config_path "$config_path" --root_path "$root_path" --root_domain "$root_domain" --sidecar_domain "$sidecar_domain" --helper_port "$helper_port" --sidecar_port "$sidecar_port" --identity "$identity" > .draft/logs/helper_sidecar.log 2>&1 & echo $! > .draft/pids/helper_sidecar.pid
