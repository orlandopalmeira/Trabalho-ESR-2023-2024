import socket
import sys
import time
import multiprocessing
import signal
import os

def ctrcl_handler(sig, frame):
    global services
    # print(f'You pressed Ctrl+C!, process id {os.getpid()}')
    for s in services: 
        s.terminate()
    sys.exit(0)
    

# Comportamento relativo ao serviço de atendimento de clientes
def handler_attend_clients(client_socket, client_address):
    data = client_socket.recv(2048)
    data = data.decode('utf-8')

    #* Processamento da mensagem recebida
    print(f"Received this data: {data}")
    time.sleep(5) # Para simular processamento demorado
    response = "Hello from the server"
    response = response.encode('utf-8')
    client_socket.send(response)

    # Fecha o socket do cliente
    client_socket.close()


# Serviço de atender clientes
def svc_attend_clients(server_ip:str, server_port:int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM = TCP; SOCK_DGRAM = UDP
    s.bind((server_ip, server_port))
    s.listen()
    print(f"Server is attending clients on {server_ip}:{server_port}")

    while True:
        try:
            client_socket, client_address = s.accept()
            print(f"Connection from {client_address} has been established!")
            # Cria uma thread para tratar do cliente
            t = multiprocessing.Process(target=handler_attend_clients, args=(client_socket, client_address))
            t.start()
        except Exception:
            print(f"Porta {server_port} fechada!")
            s.close()
            break


services = []

def main():
    adress1 = '10.0.4.10'
    t1 = multiprocessing.Process(target=svc_attend_clients, args=(adress1, 3000))
    t1.start()
    t2 = multiprocessing.Process(target=svc_attend_clients, args=(adress1, 3001))
    t2.start()
    t3 = multiprocessing.Process(target=svc_attend_clients, args=(adress1, 3002))
    t3.start()

    services.append(t1)
    services.append(t2)
    services.append(t3)
    signal.signal(signal.SIGINT, ctrcl_handler)
    

if __name__ == "__main__":
    main()
