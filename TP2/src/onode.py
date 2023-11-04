import socket
import threading
import signal
import sys
import time
from database import Database
from mensagem import Mensagem
from utils import get_ips

V_CHECK_PORT = 3001
V_START_PORT = 3002
V_STOP_PORT = 3003

# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(sig, frame):
    print("A encerrar o servidor e as threads...")
    sys.exit(0)

def thread_for_each_interface(endereço, porta, function, db: Database):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((endereço, porta))
    # print(f"Serviço '{function.__name__}' pronto para receber conexões em {endereço}:{porta}.")
    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=function, args=(dados, server_socket, addr, db)).start()
        except Exception as e:
            print(f"Erro no handler {function.__name__} com o endereço {endereço}:{porta}")
            print(e)
            break
    server_socket.close()

#!#################################################################################################################
#? Serviço extra ainda inutilizado
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
#? Serviço extra ainda inutilizado
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

#* Serviço que mostra o conteudo da routing table
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

#!#################################################################################################################
#* Serviço de CHECK_VIDEO
def handle_check_video(data: bytes, sckt, pedinte: tuple, db: Database):
    msg = Mensagem.deserialize(data)
    print(f"CHECK_VIDEO: from {pedinte[0]}, for video '{msg.get_dados()}'")
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
                vizinho = (vizinho,V_CHECK_PORT) #! serviço de check vídeo a ser atendido na porta 3003, ver melhor isto para não haver problemas de portas
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
    else:
        print(f"\n\nPORTA ERRADA A RECEBER PEDIDO DE {tipo} INCORRETAMENTE\nSUPOSTO RECEBER CHECK_VIDEOS!!!!!\n\n")

def svc_check_video(db: Database):
    service_name = "svc_check_video"
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {V_CHECK_PORT}")
    interfaces = get_ips()
    threads = []
    for itf in interfaces:
        thr=threading.Thread(target=thread_for_each_interface, args=(itf, V_CHECK_PORT, handle_check_video, db))
        thr.daemon = True
        thr.start()
        threads.append(thr)
        
    for t in threads:
        t.join()

#!#################################################################################################################
#* Serviço de START_VIDEO
#! AINDA NÃO FUNCIONA

def handle_start_video(msg, str_sckt, addr:tuple, db: Database):
    print(f"Conversação estabelecida com {addr}")

    msg = Mensagem.deserialize(msg)

    tipo = msg.get_tipo()
    pedido_id = msg.get_id()
    cliente_origem = msg.get_origem()
    from_node = addr[0]
    video = msg.get_dados()

    if tipo == Mensagem.start_video:
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
                str_sckt.sendto(start_video_msg.serialize(), (best_server, V_START_PORT))
                db.add_streaming(video, threading.Event(), addr)
                #! Cria-se aqui uma nova thread??
                relay_video(str_sckt, video, (best_server, V_START_PORT), db)

        else: 
            print(f"START_VIDEO: O video {video} não existe na rede overlay.")
            print(f"START_VIDEO: Pedido de {cliente_origem} ignorado!")
    else:
        print(f"\n\nPORTA ERRADA A RECEBER PEDIDO DE {tipo} INCORRETAMENTE\nSUPOSTO RECEBER START_VIDEOS!!!!!\n\n")

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

def svc_start_video(db: Database):
    service_name = "svc_start_video"
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {V_START_PORT}")
    interfaces = get_ips()
    threads = []
    for itf in interfaces:
        thr=threading.Thread(target=thread_for_each_interface, args=(itf, V_START_PORT, handle_start_video, db))
        thr.daemon = True
        thr.start()
        threads.append(thr)
        
    for t in threads:
        t.join()
#!#################################################################################################################

#* Serviço de STOP_VIDEO
#! - CHECKAR COMPORTAMENTO

def handle_stop_video(msg, str_sckt, addr:tuple, db: Database):
    print(f"Conversação estabelecida com {addr}")

    msg = Mensagem.deserialize(msg)

    tipo = msg.get_tipo()
    pedido_id = msg.get_id()
    cliente_origem = msg.get_origem()
    from_node = addr[0]
    video = msg.get_dados()

    if tipo == Mensagem.stop_video:
        print(db.remove_streaming(video, addr))
    else:
        print(f"\n\nPORTA ERRADA A RECEBER PEDIDO DE {tipo} INCORRETAMENTE\nSUPOSTO RECEBER STOP_VIDEOS!!!!!\n\n")

def svc_stop_video(db: Database):
    service_name = "svc_stop_video"
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {V_STOP_PORT}")
    interfaces = get_ips()
    threads = []
    for itf in interfaces:
        thr=threading.Thread(target=thread_for_each_interface, args=(itf, V_STOP_PORT, handle_stop_video, db))
        thr.daemon = True
        thr.start()
        threads.append(thr)
        
    for t in threads:
        t.join()

def main():

    # Regista o sinal para encerrar o servidor no momento do CTRL+C
    signal.signal(signal.SIGINT, ctrlc_handler)

    # Cria a base de dados
    db = Database()
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <config_file.json>")
        sys.exit(1)
    db.read_config_file(sys.argv[1])

    # Inicia os serviços em threads separadas
    svc1_thread = threading.Thread(target=svc_check_video, args=(db,))
    svc2_thread = threading.Thread(target=svc_start_video, args=(db,))
    svc3_thread = threading.Thread(target=svc_stop_video, args=(db,))
    svc51_thread = threading.Thread(target=svc_show_vizinhos, args=(db,))

    threads=[   
        svc1_thread,
        svc2_thread,
        svc3_thread,
        # svc4_thread,
        # svc5_thread,
        # svc6_thread,
        # svc51_thread,
    ]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()