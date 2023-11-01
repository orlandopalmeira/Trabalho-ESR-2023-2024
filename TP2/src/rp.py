import socket
import threading
import signal
import sys
import time
import datetime
from database_rp import Database_RP
from mensagem import Mensagem

# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(sig, frame):
    print("A encerrar o servidor e as threads...")
    sys.exit(0)

#!#################################################################################################################
#! WIP - CHECK_VIDEO AND START_VIDEO TREATMENTS

def handle_video_reqs(msg, sckt, addr:tuple, db: Database_RP):
    print(f"Conversação estabelecida com {addr}")
    print("A verificar se tem o filme pedido...")

    msg = Mensagem.deserialize(msg)

    tipo = msg.get_tipo()
    pedido_id = msg.get_id()
    cliente_origem = msg.get_origem()
    from_node = addr[0]
    video = msg.get_dados()

    if tipo == Mensagem.check_video:
        # Para os casos em que recebe um pedido de um cliente que já respondeu (esta necessidade vem do facto de o cliente fazer broadcast do pedido)
        if db.foi_respondido(pedido_id):
            print(f"Pedido do vizinho {addr} já foi respondido. Pedido ignorado.")
            return
        
        # Gestão de pedidos repetidos
        db.add_route(cliente_origem, from_node)
        print(f"Adicionada entrada {cliente_origem}:{from_node} à routing table")
        db.add_pedido_respondido(pedido_id)

        # Resposta ao pedido
        if db.servers_have_video(video):
            msg = Mensagem(Mensagem.resp_check_video, dados=True, origem="RESPONSABILIDADE") #! TEM DE SE IMPLEMENTAR A RESPONSABILIDADE DO NODO RECETOR DE PREENCHER O CAMPO "ORIGEM"
            sckt.sendto(msg.serialize(), addr)
        else:
            print("Não existe o filme pedido na rede overlay")
            pass # Ignora o pedido

        print(f"Conversação encerrada com {addr}")

    elif tipo == Mensagem.start_video:
        if db.servers_have_video(video):
            print(f"O vídeo {video} existe na rede overlay.")
            if db.is_streaming_video(video):
                print(f"O vídeo {video} já está a ser transmitido")
                #! Adicionar o addr à lista de clientes que estão a ver o video sendo assim automaticamente reenviado o video para este address
                
            else: # Vai buscar o vídeo ao melhor servidor
                best_server = db.get_best_server(video)
                start_video_msg = Mensagem(Mensagem.start_video, dados=video, origem=cliente_origem)
                stream_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                stream_socket.settimeout(5)
                stream_socket.sendto(start_video_msg.serialize(), (best_server, 3000))
                db.add_streaming(video, threading.Event(), addr)
                #! Cria-se aqui uma nova thread??
                relay_video(stream_socket, video, db)

        else: 
            print(f"O video {video} não existe na rede overlay.")
            print(f"Pedido de {cliente_origem} ignorado!")

def relay_video(sckt, video, db: Database_RP):
    while True:
        clients = db.get_clients_streaming(video)
        if len(clients) > 0:
            packet, _ = sckt.recvfrom(2048)
            for dest in clients:
                sckt.sendto(packet, dest)
        else:
            db.remove_streaming(video)
            break

def svc_video_reqs(port:int, db: Database_RP):
    service_name = "svc_check_video"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    server_socket.bind((endereco, port))
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_video_reqs, args=(dados, server_socket, addr, db)).start()
        except Exception as e:
            print(f"Erro svc_check_video: {e}")
            break

    server_socket.close()

#!#################################################################################################################
#* Solicitar a lista dos vídeos nos servidores

# Pede a um servidor os seus videos
def handler_get_videos_from_server(server_ip: str, db: Database_RP):
    """Pede a um servidor todos os seus vídeos"""
    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sckt.settimeout(6)
        server = (server_ip,3000)
        msg = Mensagem(Mensagem.check_video).serialize()
        print(f"A enviar pedido de vídeos ao servidor {server}")
        sckt.sendto(msg, server)
        try:
            data, _ = sckt.recvfrom(1024) # aguarda a resposta do servidor
        except socket.timeout:
            print(f"Timeout ao receber resposta do servidor {server}")
            return
        if data:
            videos = Mensagem.deserialize(data).get_dados()
            db.atualiza_contents(server_ip, videos)
        else:
            print(f"Resposta vazia do servidor {server_ip}")
    finally:
        sckt.close()

# V1: Solicitar vídeo aos servidores apenas uma vez
def svc_get_videos_from_servers(db: Database_RP):
    """Pede a todos os servidores os seus vídeos e adiciona-os à bd"""
    threads = []
    servers_ips = db.get_servidores()
    for server_ip in servers_ips:
        thread = threading.Thread(target=handler_get_videos_from_server, args=(server_ip, db))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


# V2: Solicitar vídeo aos servidores continuamente de 10 em 10 segundos (deve ser executada por uma thread em background)
def svc_get_videos_from_servers_continuous(db: Database_RP):
    while True:
        svc_get_videos_from_servers(db)
        time.sleep(50)

#!#################################################################################################################
#* Metricas 

# Pede a um servidor os seus videos
def handler_measure_metrics(server_ip: str, db: Database_RP):
    """Pede a um servidor todos os seus vídeos"""
    print(f"A medir métrica do servidor {server_ip}")
    num_of_requests = 10
    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sckt.settimeout(5)
        server = (server_ip, 3010)
        for i in range(num_of_requests):
            msg = Mensagem(Mensagem.metrica).serialize()
            sckt.sendto(msg, server)
            print(f"Enviada mensagem de teste {i} para o servidor {server}")

        successes = 0
        sum_delivery_time = 0
        avg_delivery_time = None
        for i in range(num_of_requests):
            try:
                data, _ = sckt.recvfrom(1024) # aguarda a resposta do 
                now = datetime.datetime.now()
                try:
                    res = Mensagem.deserialize(data)
                    successes += 1
                    sum_delivery_time += (now - res.get_timestamp()).total_seconds()
                except:
                    print(f"Erro ao deserializar resposta {i} do servidor {server}")
                    
            except socket.timeout:
                print(f"Timeout ao receber resposta {i} do servidor {server}")
                break
        if successes > 0:
            avg_delivery_time = sum_delivery_time / successes
            final_metric = 0.5 * (1 / avg_delivery_time) + 0.5 * (successes/num_of_requests) # Quanto maior a métrica, melhor
            # final_metric = (1 - (avg_delivery_time / "Max Tolerable Delay Time")) * ((successes/num_of_requests) * 100)
            db.atualiza_metrica(server_ip, final_metric)
        else:
            final_metric = 0
            db.atualiza_metrica(server_ip, final_metric) # 0 significa que está praticamente offline

        print(f"Medição de {server}: avg_del_time->{avg_delivery_time} | %success->{(successes/num_of_requests)*100}% | final_metric->{final_metric}")
    finally:
        sckt.close()

def svc_measure_metrics(db: Database_RP):
    """Pede a todos os servidores os seus vídeos e adiciona-os à bd"""
    threads = []
    servers_ips = db.get_servidores()
    for server_ip in servers_ips:
        thread = threading.Thread(target=handler_measure_metrics, args=(server_ip, db))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()

def svc_measure_metrics_continuous(db: Database_RP):
    while True:
        svc_measure_metrics(db)
        time.sleep(20) # talvez meter isto a 1 minuto

#!#################################################################################################################

#! Para debug, que mostra o conteúdo da base de dados
def svc_show_db(db: Database_RP):
    while True:
        print("-"*20); print(db); print("-"*20)
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

    print("A pedir aos servidores os seus vídeos...")
    svc_get_videos_from_servers(db)
    print("Vídeos recebidos dos servidores")

    # Inicia os serviços em threads separadas
    svc1_thread = threading.Thread(target=svc_video_reqs, args=(3000, db))
    svc2_thread = threading.Thread(target=svc_measure_metrics, args=(db,)) #! Está com o measure_metrics único, para n poluir interface
    # show_thread = threading.Thread(target=svc_show_db, args=(db,))

    threads = [
        svc1_thread,
        svc2_thread, 
        # show_thread
        ]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()