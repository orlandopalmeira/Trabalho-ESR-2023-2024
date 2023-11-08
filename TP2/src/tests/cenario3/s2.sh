#!/bin/bash

# formato: ./s2.sh <ficheiro_config>

config="./config/cenario3/s2.json"

if [ $# -eq 1 ]; then
    config=$1
fi

comando="python3 servidor.py $config"

echo "$comando"

$comando