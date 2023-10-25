import socket
import sys
import threading

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
    
    #! Pode-se alterar para o tipo especifico de mensagem
    def send(self, client_socket, message):
        client_socket.send(message.encode('utf-8'))

    #! Pode-se alterar para o tipo especifico de mensagem
    def receive(self, client_socket):
        data = client_socket.recv(1024)
        data = data.decode('utf-8')
        return data
    
    def handle_client(self, client_socket, client_address):
        data = self.receive(client_socket)

        #! Processamento da mensagem recebida
        ####Por um dicionario a ser enviado e recebido de forma serializada
        print(f"Received data from client: {data}")
        response = "Hello from the server"
        self.send(client_socket, response)

        # Fecha o socket do cliente
        client_socket.close()


    def close(self):
        self.server_socket.close()


if __name__ == "__main__":
    server_ip = '10.0.4.10'
    server_port = 3000

    try:
        server = Server(server_ip, server_port)

        server.listen()

        while True:
            client_socket, client_address = server.accept()

            #* Cria uma thread para tratar do cliente
            client_thread = threading.Thread(target=server.handle_client, args=(client_socket, client_address))
            client_thread.start()
    
    finally:
        server.close()
