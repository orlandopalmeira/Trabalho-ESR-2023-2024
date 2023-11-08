#!/bin/bash

# formato: ./o3.sh <ficheiro_config>

config="./config/cenario3/o3.json"

if [ $# -eq 1 ]; then
    config=$1
fi

comando="python3 onode.py $config"

echo "$comando"

$comando