#!/bin/bash
# formato: ./c3.sh <video> (<video> opcional)

config="./config/cenario3/c3.json"
video="movie.Mjpeg"

if [ $# -eq 1 ]; then
    video=$1
fi

comando="python3 cliente.py $config $video"

#Imprime o comando
echo "$comando"

# Executa o comando
$comando