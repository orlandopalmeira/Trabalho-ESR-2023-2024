import subprocess
import socket 
import sys

def get_ips():
    command = "ip -4 addr show | grep inet | awk '{print $2}' | cut -d'/' -f1"
    # Executa o comando e captura o output
    processo = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, erro = processo.communicate()
    
    # Tratamento do output
    lista = output.decode('utf-8').split('\n')
    
    ips = [ip for ip in lista if ip not in {'','127.0.0.1'}]

    return ips

def hostname():
    return socket.gethostname()

def change_terminal_title():
    sys.stdout.write(f"\033]0;{hostname()}\007")
    sys.stdout.flush()