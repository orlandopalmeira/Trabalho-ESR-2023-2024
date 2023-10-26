import socket
import sys
import time
import threading
import os


# Comportamento relativo ao serviço de atendimento de clientes
def handle_attend_clients(client_socket, client_address):
    data = client_socket.recv(2048)
    data = data.decode('utf-8')
    print(f"Received this data: {data}")

    #* Processamento da mensagem recebida
    time.sleep(5) # Para simular processamento demorado

    response = "Hello from the server"
    client_socket.send(response.encode('utf-8'))

    # Fecha o socket do cliente
    client_socket.close()


# Serviço de atendimento de clientes
def svc_attend_clients(server_ip:str, server_port:int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endereco = server_ip
    porta = server_port
    s.bind((endereco, porta))
    s.listen()
    print(f"Estou à escuta em {endereco}:{porta}")

    while True:
        try:
            client_socket, client_address = s.accept()
            print(f"Connection from {client_address} has been established!")
            # Cria uma thread para tratar do cliente
            t = threading.Thread(target=handle_attend_clients, args=(client_socket, client_address))
            t.start()
        except Exception:
            break

    s.close()


def main():
    threading.Thread(target=svc_attend_clients, args=('10.0.4.10', 3000)).start()
    threading.Thread(target=svc_attend_clients, args=('10.0.4.10', 3001)).start()
    threading.Thread(target=svc_attend_clients, args=('10.0.4.10', 3002)).start()

if __name__ == "__main__":
    main()
