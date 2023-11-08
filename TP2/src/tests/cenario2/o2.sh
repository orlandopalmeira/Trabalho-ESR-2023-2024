#!/bin/bash

# formato: ./o2.sh <ficheiro_config>

config="./config/cenario2/o2.json"

if [ $# -eq 1 ]; then
    config=$1
fi

comando="python3 onode.py $config"

echo "$comando"

$comando