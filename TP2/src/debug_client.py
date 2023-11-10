import socket
import sys
from mensagem import Mensagem
from utils import get_ips

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


vizinhos = ["10.0.18.1", "10.0.19.2", "10.0.16.1", "10.0.17.1"]

vizinhos_addr = [(ip, 3041) for ip in vizinhos]

msg = "hello"
msg=msg.encode('utf-8')

for v in vizinhos_addr:
    s.sendto(msg, v)


s.close()
