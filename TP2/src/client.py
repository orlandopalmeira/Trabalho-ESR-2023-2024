import socket
import sys


if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    #* Se quisermos associar uma porta especifica ao cliente
    # client_ip = "localhost"
    # client_port = 3030
    # client.bind(client_ip, client_port)

    destination_ip = '10.0.4.10'
    destination_port = int(sys.argv[1])
    addr = (destination_ip, destination_port)
    # client.connect(addr) # For TCP


    message = "Olá, servidor"
    message = message.encode('utf-8')
    # client.send(message) # For TCP
    client.sendto(message, addr)

    resposta, add = client.recvfrom(1024)
    resposta = resposta.decode('utf-8')
    print(f"Resposta do servidor: {resposta}")

    client.close()
