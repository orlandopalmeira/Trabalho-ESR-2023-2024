#!/bin/bash

# formato: ./s1.sh <ficheiro_config>

config="./config/cenario2/s1.json"

if [ $# -eq 1 ]; then
    config=$1
fi

comando="python3 servidor.py $config"

echo "$comando"

$comando