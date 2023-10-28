import socket
import sys
from mensagem import Mensagem


if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    #* Se quisermos associar uma porta especifica ao cliente
    # client_ip = "localhost"
    # client_port = 3030
    # client.bind(client_ip, client_port)

    # destination_ip = '10.0.4.10'
    destination_ip = int(sys.argv[1])
    destination_port = int(sys.argv[2])
    addr = (destination_ip, destination_port)
    # client.connect(addr) # For TCP

    my_ip = sys.argv[3]

    message = "Olá, servidor"
    message = Mensagem(Mensagem.video, my_ip, "video.Mpjeg").serialize()
    # client.send(message) # For TCP
    client.sendto(message, addr)

    resposta, add = client.recvfrom(1024)
    resposta = resposta.decode('utf-8')
    print(f"Resposta do servidor: {resposta}")

    client.close()
