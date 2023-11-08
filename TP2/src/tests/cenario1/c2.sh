#!/bin/bash

# formato: ./c2.sh <video> (<video> opcional)

config="./config/cenario1/c2.json"
video="movie.Mjpeg"

if [ $# -eq 1 ]; then
    video=$1
fi

comando="python3 cliente.py $config $video"

#Imprime o comando
echo "$comando"

# Executa o comando
$comando