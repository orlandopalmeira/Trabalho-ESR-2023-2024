import socket
import sys
import time
# import threading
import multiprocessing
import signal
import os

class Server:
    def __init__(self, ip:str, port:int):
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM = TCP; SOCK_DGRAM = UDP
        self.server_socket.bind((self.ip, self.port))

    def listen(self):
        self.server_socket.listen()
        print(f"Server is listening on {self.ip}:{self.port}")

    def accept(self):
        client_socket, client_address = self.server_socket.accept()
        print(f"Received connection from {client_address}")
        return client_socket, client_address
    
    def send(self, client_socket, message):
        client_socket.send(message.encode('utf-8'))

    def receive(self, client_socket):
        data = client_socket.recv(1024)
        data = data.decode('utf-8')
        return data
    
    def close(self):
        self.server_socket.close()
    

def handle_client(server, client_socket, client_address):
    data = server.receive(client_socket)

    #* Processamento da mensagem recebida
    #### Por um dicionario a ser enviado e recebido de forma serializada
    print(f"Received data from client: {data}")
    response = "Hello from the server"
    time.sleep(5) # Para simular processamento demorado

    server.send(client_socket, response)

    # Fecha o socket do cliente
    client_socket.close()



def attend_clients(server_ip:str, server_port:int):
    # print(f'ID process on port {server_port}: {os.getpid()}')
    server = Server(server_ip, server_port)
    server.listen()
    run = True
    while run:
        try:
            client_socket, client_address = server.accept()
            # Cria uma thread para tratar do cliente
            client_thread = multiprocessing.Process(target=handle_client, args=(server, client_socket, client_address))
            client_thread.start()
        except Exception:
            run = False
            print(f"{server_port} fechado!!!!!")
            server.close()
            # break


services = []

def ctrcl_handler(sig, frame):
    global services
    # print(f'You pressed Ctrl+C!, process id {os.getpid()}')
    for s in services: 
        s.terminate()
    sys.exit(0)

def main():
    t1 = multiprocessing.Process(target=attend_clients, args=('10.0.4.10', 3000))
    t1.start()
    t2 = multiprocessing.Process(target=attend_clients, args=('10.0.4.10', 3001))
    t2.start()
    t3 = multiprocessing.Process(target=attend_clients, args=('10.0.4.10', 3002))
    t3.start()

    services.append(t1)
    services.append(t2)
    services.append(t3)
    signal.signal(signal.SIGINT, ctrcl_handler)
    

if __name__ == "__main__":
    main()
