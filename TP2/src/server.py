import socket
import threading
import signal
import sys
import time
from database import Database

# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(sig, frame):
    print("A encerrar o servidor e as threads...")
    sys.exit(0)


# Função para lidar com os clientes do serviço svc_attend_clients
def handle_attend_clients(client_socket, address:tuple, db: Database):
    print(f"Conexão estabelecida com {address}")
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        response = f"{data.upper().decode('utf-8')}"
        time.sleep(3)
        client_socket.send(response.encode('utf-8'))
    print(f"Conexão encerrada com {address}")
    client_socket.close()

# Função que lida com o serviço svc_attend_clients
def svc_attend_clients(port:int, db: Database):
    service_name = "svc_attend_clients"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    server_socket.bind((endereco, port))
    server_socket.listen()
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_attend_clients, args=(client_socket, addr, db))
        client_handler.start()


# Função para lidar com os clientes do serviço de atender clientes. !Genérico!
def handle_add_vizinhos(client_socket, address:tuple, db: Database):
    print(f"Conexão estabelecida com {address}")
    while True:
        data = client_socket.recv(1024)
        if not data:
            break

        db.add_vizinho(address[0])
        time.sleep(3)

        response = f"{address} adicionado com sucesso"
        client_socket.send(response.encode('utf-8'))
        
    print(f"Conexão encerrada com {address}")
    client_socket.close()

# Função que lida com o serviço de adicionar vizinhos
def svc_add_vizinhos(port:int, db: Database):
    service_name = 'svc_add_vizinhos'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    server_socket.bind((endereco, port))
    server_socket.listen()
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_add_vizinhos, args=(client_socket, addr, db))
        client_handler.start()


# Função que lida com o serviço de mostrar vizinhos de 5 em 5 segundos
def svc_show_vizinhos(db: Database):
    service_name = 'svc_show_vizinhos'
    print(f"Serviço {service_name} pronto para mostrar vizinhos de 5 em 5 segundos.")
    while True:
        db.show_vizinhos()
        time.sleep(5)

def main():
    # Regista o sinal para encerrar o servidor no momento do CTRL+C
    signal.signal(signal.SIGINT, ctrlc_handler)

    db = Database()

    # Inicia os serviços em threads separadas
    service1_thread = threading.Thread(target=svc_attend_clients, args=(3000, db))
    service2_thread = threading.Thread(target=svc_add_vizinhos, args=(3001, db))
    service3_thread = threading.Thread(target=svc_show_vizinhos, args=(db,))

    threads = [service1_thread, service2_thread, service3_thread]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()