import socket
import threading
import signal
import sys
import time

# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(sig, frame):
    print("A encerrar o servidor e as threads...")
    sys.exit(0)

# Função para lidar com os clientes do serviço svc_attend_clients
def handle_attend_clients(client_socket, address):
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
def svc_attend_clients(service_name:str, port:int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endereco = '10.0.4.10'
    server_socket.bind((endereco, port))
    server_socket.listen()
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_attend_clients, args=(client_socket, addr))
        client_handler.start()


def main():
    # Regista o sinal para encerrar o servidor no momento do CTRL+C
    signal.signal(signal.SIGINT, ctrlc_handler)

    # Inicia os serviços em threads separadas
    service1_thread = threading.Thread(target=svc_attend_clients, args=('Serviço 1', 3000))
    service2_thread = threading.Thread(target=svc_attend_clients, args=('Serviço 2', 3001))
    service3_thread = threading.Thread(target=svc_attend_clients, args=('Serviço 3', 3002))

    threads = [service1_thread, service2_thread, service3_thread]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()