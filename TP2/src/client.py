import socket
import sys


if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM = TCP; SOCK_DGRAM = UDP
    
    #* Se quisermos associar uma porta especifica ao cliente
    # client_ip = "localhost"
    # client_port = 3030
    # client.bind(client_ip, client_port)

    destination_ip = '10.0.4.10'
    destination_port = int(sys.argv[1])
    client.connect((destination_ip, destination_port))


    message = "Olá, servidor"
    message = message.encode('utf-8')
    client.send(message)

    resposta = client.recv(1024)
    resposta = resposta.decode('utf-8')
    print(f"Resposta do servidor: {resposta}")

    client.close()
