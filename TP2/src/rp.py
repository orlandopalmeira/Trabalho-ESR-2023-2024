import socket
import threading
import signal
import sys
import time
from database_rp import Database_RP
from mensagem import Mensagem

# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(sig, frame):
    print("A encerrar o servidor e as threads...")
    sys.exit(0)

#!#################################################################################################################
#! WIP
# Verifica se tem o filme pedido e adiciona o cliente à sua routingTable
def handle_check_video(msg, socket, addr:tuple, db: Database_RP):
    print(f"Conversação estabelecida com {addr}")
    print("A verificar se tem o filme pedido...")

    msg = Mensagem.deserialize(msg)

    pedido_id = msg.get_id()
    cliente_origem = msg.get_origem()
    from_node = addr[0]
    video = msg.get_dados()

    # Para os casos em que recebe um pedido de um cliente que já respondeu (esta necessidade vem do facto de o cliente fazer broadcast do pedido)
    if not db.foi_respondido(pedido_id):
        db.add_route(cliente_origem, from_node)
        print(f"Adicionada entrada {cliente_origem}:{from_node} à routing table")
        db.add_pedido_respondido(pedido_id)
    else:
        print("Pedido já foi respondido")

    response = "Sucesso!"
    socket.sendto(response.encode('utf-8'), addr)
    print(f"Conversação encerrada com {addr}")

# Serviço relativo à verificação se tem o filme pedido e adiciona o cliente à sua routingTable
def svc_check_video(port:int, db: Database_RP):
    service_name = "svc_check_video"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    server_socket.bind((endereco, port))
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_check_video, args=(dados, server_socket, addr, db)).start()
        except Exception as e:
            print(f"Erro svc_check_video: {e}")
            break

    server_socket.close()

#!#################################################################################################################
#* Solicitar vídeos aos servidores

# Pede a um servidor os seus videos
def get_videos_from_server(server_ip, sckt, db: Database_RP):
    """Pede a um servidor todos os seus vídeos"""
    server = (server_ip,3000)
    msg = Mensagem(Mensagem.check_video, "dummy_ip", None).serialize()
    sckt.sendto(msg, server)
    data = sckt.recvfrom(1024) # aguarda a resposta do servidor
    if data:
        videos = Mensagem.deserialize(data).get_dados()
        db.adiciona_fonte(server_ip, 0.0, videos)
    sckt.close()

# V1: Solicitar vídeo aos servidores apenas uma vez
def get_videos_from_servers(servers_ips, db: Database_RP):
    """Pede a todos os servidores os seus vídeos e adiciona-os à bd"""
    threads = []
    for server_ip in servers_ips:
        sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        thread = threading.Thread(target=get_videos_from_server, args=(server_ip, sckt, db))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


# V2: Solicitar vídeo aos servidores continuamente de 10 em 10 segundos (deve ser executada por uma thread em background)
def get_videos_from_servers_continuous(servers_ips, db: Database_RP):
    while True:
        get_videos_from_servers(servers_ips,db)
        time.sleep(10)

#!#################################################################################################################

def main():

    db = Database_RP()
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <config_file.json>")
        sys.exit(1)
    db.read_config_file(sys.argv[1])

    # Regista o sinal para encerrar o servidor no momento do CTRL+C
    signal.signal(signal.SIGINT, ctrlc_handler)

    

    # Inicia os serviços em threads separadas
    svc1_thread = threading.Thread(target=svc_check_video, args=(3000, db))
    svc2_thread = threading.Thread(target=svc_update_metrics, args=(3001, db))

    threads = [svc1_thread, svc2_thread]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()