import socket

class Client:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM = TCP; SOCK_DGRAM = UDP

    def bind(self, client_ip:str, client_port:int):
        self.client_socket.bind((client_ip, client_port))

    def connect(self, destination_ip:str, destination_port:int):
        self.client_socket.connect((destination_ip, destination_port))

    def send(self, message):
        self.client_socket.send(message.encode('utf-8'))

    def receive(self):
        response = self.client_socket.recv(1024)
        response = response.decode('utf-8')

        return response

    def close(self):
        self.client_socket.close()


if __name__ == "__main__":
    client = Client()

    destination_ip = '10.0.4.10'
    destination_port = 3000
    client.connect(destination_ip, destination_port)

    client.send("Olá, servidor")

    resposta = client.receive()
    print(f"Resposta do servidor: {resposta}")

    client.close()
