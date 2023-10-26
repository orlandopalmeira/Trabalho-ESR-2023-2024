import socket
import sys

def main():
    s : socket.socket
    mensagem : str
    endereco : str
    porta : int

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '10.0.0.10'

    print(sys.argv[0])
    porta = int(sys.argv[1])

    mensagem = "Adoro Redes :)"

    s.sendto(mensagem.encode('utf-8'), (endereco, porta))

    msg, add = s.recvfrom(1024)

    print(f"Recebi {msg.decode('utf-8')} do {add}")

if __name__ == '__main__':
    main()
