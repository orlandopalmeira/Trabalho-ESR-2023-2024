import socket
import threading
import time
import database

def processamento(mensagem : bytes, add : tuple, s : socket.socket, cenas : database):
    cenas.acrescenta(add)
    s.sendto("Correu bem!".encode('utf-8'), add)

def processamento2(mensagem : bytes, add : tuple, s : socket.socket, cenas : database):
    cenas.remove(add)
    s.sendto("SUCESIUM!".encode('utf-8'), add)

def servico(cenas:database):
    s : socket.socket
    endereco : str
    porta : int
    mensagem : bytes
    add : tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '10.0.4.10'
    porta = 3000

    s.bind((endereco, porta))

    print(f"Estou à escuta em {endereco}:{porta}")

    while True:
        try:
            mensagem, add = s.recvfrom(1024)
            threading.Thread(target=processamento, args=(mensagem, add, s, cenas)).start()
        except Exception:
            break

    s.close()

def servico2(cenas:database):
    s : socket.socket
    endereco : str
    porta : int
    mensagem : bytes
    add : tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '10.0.4.10'
    porta = 4000

    s.bind((endereco, porta))

    print(f"Estou à escuta em {endereco}:{porta}")

    while True:
        try:
            mensagem, add = s.recvfrom(1024)
            threading.Thread(target=processamento2, args=(mensagem, add, s, cenas)).start()
        except Exception:
            break

    s.close()

def servico3(cenas:database):
    while True:
       cenas.show() 

def main():
    cenas : database.database

    cenas = database.database()
    threading.Thread(target=servico, args=(cenas,)).start()
    threading.Thread(target=servico2, args=(cenas,)).start()
    threading.Thread(target=servico3, args=(cenas,)).start()           

if __name__ == '__main__':
    main()