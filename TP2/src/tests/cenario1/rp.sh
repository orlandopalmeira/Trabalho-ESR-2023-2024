#!/bin/bash

# formato: ./rp.sh <ficheiro_config>

config="./config/cenario1/rp.json"

if [ $# -eq 1 ]; then
    config=$1
fi

comando="python3 rp.py $config"

echo "$comando"

$comando