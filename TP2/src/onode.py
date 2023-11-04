import socket
import threading
import signal
import sys
import time
from database import Database
from mensagem import Mensagem

# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(sig, frame):
    print("A encerrar o servidor e as threads...")
    sys.exit(0)

#!#################################################################################################################

# Função para lidar com os clientes do serviço svc_attend_clients
def handle_attend_clients(dados, socket, addr:tuple, db: Database):
    print(f"Conversação estabelecida com {addr}")

    # Processamento da mensagem
    response = f"{dados.upper().decode('utf-8')}"
    time.sleep(3)

    socket.sendto(response.encode('utf-8'), addr)
    print(f"Conversação encerrada com {addr}")

# Função que lida com o serviço svc_attend_clients
def svc_attend_clients(port:int, db: Database):
    service_name = "svc_attend_clients"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    server_socket.bind((endereco, port))
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_attend_clients, args=(dados, server_socket, addr, db)).start()
        except Exception as e:
            print(f"Erro svc_attend_clients: {e}")
            break

    server_socket.close()

#!#################################################################################################################

# Função para lidar com o serviço svc_add_vizinhos
def handle_add_vizinhos(dados, socket, addr:tuple, db: Database):
    print(f"Conversação estabelecida com {addr}")

    db.add_vizinho(addr[0])
    time.sleep(3)

    response = f"{addr[0]} adicionado com sucesso"
    socket.sendto(response.encode('utf-8'), addr)

    print(f"Conversação encerrada com {addr}")

# Função que lida com o serviço de adicionar vizinhos
def svc_add_vizinhos(port:int, db: Database):
    service_name = 'svc_add_vizinhos'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    server_socket.bind((endereco, port))
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_add_vizinhos, args=(dados, server_socket, addr, db)).start()
        except Exception as e:
            print(f"Erro svc_add_vizinhos: {e}")
            break

    server_socket.close()

#!#################################################################################################################

# Função para lidar com o serviço svc_add_vizinhos
def handle_remove_vizinhos(dados, socket, addr:tuple, db: Database):
    print(f"Conversação estabelecida com {addr}")
    
    response = db.remove_vizinho(addr[0])
    time.sleep(3)
    print(f"Removendo vizinho...{addr[0]}")

    socket.sendto(response.encode('utf-8'), addr)
    
    print(f"Conversação encerrada com {addr}")

# Função que lida com o serviço de adicionar vizinhos
def svc_remove_vizinhos(port:int, db: Database):
    service_name = 'svc_remove_vizinhos'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    addr = (endereco, port)
    server_socket.bind(addr)

    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_remove_vizinhos, args=(dados, server_socket, addr, db)).start()
        except Exception as e:
            print(f"Erro svc_remove_vizinhos: {e}")
            break
    server_socket.close()

#!#################################################################################################################

# Função que lida com o serviço de mostrar vizinhos de 5 em 5 segundos
def svc_show_vizinhos(db: Database):
    service_name = 'svc_show_vizinhos'
    print(f"Serviço '{service_name}' pronto para mostrar vizinhos de 5 em 5 segundos.")
    while True:
        # res = db.get_vizinhos()
        res = db.get_routing_table()
        print(f"Routing Table: {res}")
        time.sleep(5)

#!#################################################################################################################
#! COPIED FROM RP.PY - UNFINISHED - VAI SER NECESSÁRIO RECOPIAR O CODIGO DO RP.PY
#* CHECK_VIDEO and START_VIDEO treatments


def handle_video_reqs(msg, str_sckt, addr:tuple, db: Database):
    print(f"Conversação estabelecida com {addr}")

    msg = Mensagem.deserialize(msg)

    tipo = msg.get_tipo()
    pedido_id = msg.get_id()
    cliente_origem = msg.get_origem()
    from_node = addr[0]
    video = msg.get_dados()

    if tipo == Mensagem.check_video:
        handle_check_video_req(msg.serialize(),addr,str_sckt,db) #! Isto é apenas para teste.
        # # Para os casos em que recebe um pedido de um cliente que já respondeu (esta necessidade vem do facto de o cliente fazer broadcast do pedido)
        # if db.foi_respondido(pedido_id):
        #     print(f"CHECK_VIDEO: Pedido do vizinho {addr} já foi respondido. Pedido ignorado.")
        #     return
        
        # # Gestão de pedidos repetidos
        # db.add_route(cliente_origem, from_node)
        # print(f"CHECK_VIDEO: Adicionada entrada {cliente_origem}:{from_node} à routing table")
        # db.add_pedido_respondido(pedido_id)

        # # Resposta ao pedido
        # if db.servers_have_video(video):
        #     msg = Mensagem(Mensagem.resp_check_video, dados=True, origem="RESPONSABILIDADE") #! TEM DE SE IMPLEMENTAR A RESPONSABILIDADE DO NODO RECETOR DE PREENCHER O CAMPO "ORIGEM"
        #     str_sckt.sendto(msg.serialize(), addr)
        # else:
        #     print("CHECK_VIDEO: Não existe o filme pedido na rede overlay")
        #     pass # Ignora o pedido

        # print(f"CHECK_VIDEO: Conversação encerrada com {addr}")

    elif tipo == Mensagem.start_video:
        if db.servers_have_video(video):
            print(f"START_VIDEO: O vídeo {video} existe na rede overlay.")
            if db.is_streaming_video(video):
                print(f"START_VIDEO: O vídeo {video} já está a ser transmitido")
                db.add_streaming(video, threading.Event(), addr)
                
            else: # Vai buscar o vídeo ao melhor servidor
                best_server = db.get_best_server(video)
                start_video_msg = Mensagem(Mensagem.start_video, dados=video, origem="RESPONSABILIDADE")
                str_sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                str_sckt.settimeout(5)
                str_sckt.sendto(start_video_msg.serialize(), (best_server, 3000))
                db.add_streaming(video, threading.Event(), addr)
                #! Cria-se aqui uma nova thread??
                relay_video(str_sckt, video, (best_server, 3000), db)

        else: 
            print(f"START_VIDEO: O video {video} não existe na rede overlay.")
            print(f"START_VIDEO: Pedido de {cliente_origem} ignorado!")
    elif tipo == Mensagem.stop_video:
        video = msg.get_dados()
        print(db.remove_streaming(video, addr))

def relay_video(str_sckt, video, server: tuple, db: Database):
    print("Hello from relay_video")
    while True:
        clients = db.get_clients_streaming(video) # clientes/dispositivos que querem ver o vídeo
        print('len clients: ', len(clients))
        if len(clients) > 0: # ainda existem clientes a querer ver o vídeo?
            packet, _ = str_sckt.recvfrom(20480) #! Aqui pode ser necessário indicar um socket timeout para o caso do servidor deixar de enviar o video
            for dest in clients: # envia o frame recebido do servidor para todos os dispositivos a ver o vídeo
                str_sckt.sendto(packet, dest)
        else: # não existem mais dispositivos a querer ver o vídeo
            break # pára a stream
        
    stop_video_msg = Mensagem(Mensagem.stop_video, dados=video).serialize()
    str_sckt.sendto(stop_video_msg, server)
    str_sckt.close() 
    print(f"Streaming de '{video}' terminada")

def svc_video_reqs(port:int, db: Database):
    service_name = "svc_video_reqs"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    server_socket.bind((endereco, port))
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_video_reqs, args=(dados, server_socket, addr, db)).start()
        except Exception as e:
            print(f"Erro svc_video_reqs: {e}")
            break

    server_socket.close()

#!#################################################################################################################
#* Serviço de check_video
def handle_check_video_req(data: bytes, pedinte: tuple, sckt, db: Database):
    msg = Mensagem.deserialize(data)
    tipo = msg.get_tipo()
    if tipo == Mensagem.check_video: #> para evitar responder a pedidos que não sejam deste tipo 
        video = msg.get_dados()
        if db.is_streaming_video(video): #> o nodo está já a transmitir o vídeo => Tem o vídeo
            response = Mensagem(Mensagem.resp_check_video, dados=True, origem=sckt.getsockname()[0]) #! isto do getsockname tem de ser testado
            sckt.sendto(response, pedinte)
        else: #> o nodo ainda não está a transmitir o video => não tem o vídeo
            vizinhos = db.get_vizinhos_for_broadcast(pedinte[0])
            msg_para_vizinhos = msg.serialize() #> para pedir o check video aos vizinhos (reaproveita a mensagem do cliente para manter o ID)
            vizinhos_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #> este socket serve apenas para ele perguntar aos vizinhos se eles têm o vídeo 
            vizinhos_socket.settimeout(5) #> Se o vizinho não encontrar o vídeo ele não responde, pelo que temos de definir um tempo máximo de espera. Se ultrapassar esse tempo, assumimos que o vizinho não encontrou nada.

            # Check video aos vizinhos
            for vizinho in vizinhos:
                vizinho = (vizinho,3000) #! serviço de check vídeo a ser atendido na porta 3003, ver melhor isto para não haver problemas de portas
                vizinhos_socket.sendto(msg_para_vizinhos, vizinho) #> faz um check_video ao vizinho
                
            # Recepção das respostas dos vizinhos
            for vizinho in vizinhos: #> verifica respostas dos vizinhos até encontrar uma que indique alguém que tenha o vídeo
                try:
                    resp_vizinho, _ = vizinhos_socket.recvfrom(1024) #> vizinho responde a indicar quem tem o vídeo
                    resp_vizinho = Mensagem.deserialize(resp_vizinho) #> resposta do vizinho
                    if resp_vizinho.get_dados(): #> o vizinho tem o vídeo
                        sckt.sendto(resp_vizinho.serialize(), pedinte) #> envia a resposta do vizinho com as informações necessárias
                        break #> termina a recepção de mensagens porque já encontrou quem tem o vídeo
                except socket.timeout: 
                    pass
            
            vizinhos_socket.close()

def svc_check_video(port:int, db: Database):
    service_name = "svc_check_video"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    server_socket.bind((endereco, port))
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_check_video_req, args=(dados,addr,server_socket,db)).start()
        except Exception as e:
            print(f"Erro svc_video_reqs: {e}")
            break
    server_socket.close()

#!#################################################################################################################

def main():

    db = Database()
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <config_file.json>")
        sys.exit(1)
    db.read_config_file(sys.argv[1])

    # Regista o sinal para encerrar o servidor no momento do CTRL+C
    signal.signal(signal.SIGINT, ctrlc_handler)

    # Inicia os serviços em threads separadas
    svc1_thread = threading.Thread(target=svc_video_reqs, args=(3000, db))
    svc2_thread = threading.Thread(target=svc_add_vizinhos, args=(3001, db))
    svc3_thread = threading.Thread(target=svc_remove_vizinhos, args=(3002, db))
    # svc4_thread = threading.Thread(target=svc_check_video, args=(3003,db))
    svc5_thread = threading.Thread(target=svc_attend_clients, args=(3004, db))
    svc6_thread = threading.Thread(target=svc_show_vizinhos, args=(db,))

    threads=[   
        svc1_thread,
        svc2_thread,
        svc3_thread,
        # svc4_thread,
        svc5_thread,
        svc6_thread
    ]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()