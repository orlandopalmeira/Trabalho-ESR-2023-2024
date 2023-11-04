import socket
import sys
from mensagem import Mensagem
from utils import get_ips

if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    #* Se quisermos associar uma porta especifica ao cliente
    # client_ip = "localhost"
    # client_port = 3030
    # client.bind(client_ip, client_port)

    # destination_ip = '10.0.4.10'
    destination_ip = sys.argv[1]
    destination_port = 3000
    if len(sys.argv) >= 3:
        destination_port = int(sys.argv[2])

    addr = (destination_ip, destination_port)

    # my_ip = sys.argv[3]

    # message = message.encode('utf-8')
    message = Mensagem(Mensagem.check_video, dados="movie.Mjpeg", origem=get_ips()[0])
    print(f"Mensagem a ser enviada:\n {message}\n" + "-"*30 )

    client.sendto(message.serialize(), addr)

    response, _ = client.recvfrom(1024)
    response = Mensagem.deserialize(response)
    print(f"Resposta obtida:\n {response}")

    # resposta, add = client.recvfrom(1024)
    # resposta = resposta.decode('utf-8')
    # print(f"Resposta do servidor: {resposta}")

    client.close()
