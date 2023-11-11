import socket
import threading
import signal
import sys
import time
from database import Database
from mensagem import Mensagem
from utils import get_ips
from queue import Queue
from functools import partial

V_CHECK_PORT = 3001 #> Porta de atendimento do serviço check_videos
V_START_PORT = 3002 #> Porta de atendimento do serviço start_videos
V_STOP_PORT  = 3003 #> Porta de atendimento do serviço stop_videos
ADD_VIZINHO_PORT= 3005 #> Porta de atendimento do serviço add_vizinho
RMV_VIZINHO_PORT= 3006 #> Porta de atendimento do serviço rmv_vizinho


# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(db: Database, sig, frame):
    print("A encerrar o servidor e as threads...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = Mensagem(Mensagem.rmv_vizinho)
    msg = msg.serialize()
    for v in db.get_vizinhos():
        s.sendto(msg, (v, RMV_VIZINHO_PORT)) #! Não espero por nenhum ACK
        print(f"Enviado pedido de remoção de vizinho para {v}")
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

##################################################################################################################
#* Serviço de arranque que notifica vizinhos da sua inicialização

def handle_notify_vizinhos(vizinho: tuple, sckt, cur_retries = 0):
    MAX_RETRIES = 2
    msg = Mensagem(Mensagem.add_vizinho).serialize()
    sckt.sendto(msg, vizinho)
    try:
        resp, _ = sckt.recvfrom(2048)
        resp = Mensagem.deserialize(resp)
        if resp.get_tipo() == Mensagem.add_vizinho:
            print(f"Vizinho {vizinho[0]} notificado com sucesso.")
        else:
            print(f"Vizinho {vizinho[0]} NÃO respondeu como esperado!!!")
        sckt.close()
    except socket.timeout:
        print(f"Timeout {vizinho[0]} DEBUG")
        cur_retries += 1
        if cur_retries < MAX_RETRIES:
            handle_notify_vizinhos(vizinho, sckt, cur_retries=cur_retries)
        else:
            print(f"Não consegui notificar {vizinho[0]}")
            sckt.close()


def svc_notify_vizinhos(db: Database):
    vizinhos = db.get_vizinhos()
    vizinhos_addr = [(vizinho, ADD_VIZINHO_PORT) for vizinho in vizinhos]
    print(f"A notificar os vizinhos {vizinhos}.")
    threads = [] #! Caso se queira esperar por todas as threads

    for v in vizinhos_addr:
        sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sckt.settimeout(2)
        t=threading.Thread(target=handle_notify_vizinhos, args=(v,sckt))
        t.start()
        threads.append(t)
        # break #! DEBUG

    for t in threads:
        t.join()

##################################################################################################################
#* Serviço de ADD_VIZINHOS
# Função para lidar com o serviço svc_add_vizinhos
def handle_add_vizinhos(msg, socket, addr:tuple, db: Database):
    print(f"ADD_VIZINHO: recebido de {addr[0]}")
    msg = Mensagem.deserialize(msg)
    if not msg.get_tipo() == Mensagem.add_vizinho:
        print(f"ADD_VIZINHO: pedido de {addr[0]} não é do tipo ADD_VIZINHO")
        return
    
    db.add_vizinho(addr[0])

    msg.set_dados("ACK")
    response = msg.serialize()
    socket.sendto(response, addr)

    print(f"ADD_VIZINHO: {addr[0]} adicionado aos vizinhos com sucesso.")

# Função que lida com o serviço de adicionar vizinhos
def svc_add_vizinhos(db: Database):
    service_name = 'svc_add_vizinhos'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    port = ADD_VIZINHO_PORT
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

##################################################################################################################
#* Serviço de REMOVE_VIZINHOS 
# Função para lidar com o serviço svc_add_vizinhos
def handle_remove_vizinhos(msg, addr:tuple, db: Database):
    print(f"REMOVE_VIZINHO: recebido de {addr[0]}")
    msg = Mensagem.deserialize(msg)
    if not msg.get_tipo() == Mensagem.rmv_vizinho: # mensagem será de tipo diferente
        print(f"REMOVE_VIZINHO: pedido de {addr[0]} não é do tipo RMV_VIZINHO")
        return
    
    r = db.remove_vizinho(addr[0])
    if r == 1:
        print(f"REMOVE_VIZINHO: {addr[0]} NÃO EXISTIA na lista de vizinhos!!!!!")
    else:
        print(f"REMOVE_VIZINHO: {addr[0]} removido dos vizinhos com sucesso.")
        #! Talvez tbm tenha remover o streaming, caso haja algum streaming a ser enviado para ele, ou passar isso para a responsabilidade do rmv_vizinho

# Função que lida com o serviço de adicionar vizinhos
def svc_remove_vizinhos(db: Database):
    service_name = 'svc_remove_vizinhos'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = '0.0.0.0' # Listen on all interfaces
    port = RMV_VIZINHO_PORT
    addr = (endereco, port)
    server_socket.bind(addr)

    print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_remove_vizinhos, args=(dados, addr, db)).start()
        except Exception as e:
            print(f"Erro svc_remove_vizinhos: {e}")
            break
    server_socket.close()

##################################################################################################################
#* Serviço que mostra a base de dados
# Função que lida com o serviço de mostrar vizinhos quando é premido ENTER
def svc_show_db(db: Database):
    service_name = 'svc_show_db'
    interval = 15
    print(f"Serviço '{service_name}' pronto para mostrar a dbde {interval} em {interval} segundos. (DEBUG)")
    while True:
        print(db)
        time.sleep(interval)

##################################################################################################################

#* Serviço que limpa os pedidos respondidos da base de dados
def svc_clear_pedidos_resp(db: Database):
    service_name = 'svc_clear_pedidos_resp'
    interval = 15
    max_age_secs = 10
    print(f"Serviço '{service_name}' a limpar pedidos já respondidos há mais de {max_age_secs} de {interval} em {interval} segundos.")
    while True:
        db.remove_pedidos_respondidos(max_age_secs)
        time.sleep(interval)

##################################################################################################################
#* Serviço de CHECK_VIDEO
def handle_check_video(data: bytes, sckt, pedinte: tuple, db: Database):
    msg = Mensagem.deserialize(data)
    db.add_route(msg.get_origem(), pedinte[0]) 
    tipo = msg.get_tipo()
    if tipo == Mensagem.check_video: #> para evitar responder a pedidos que não sejam deste tipo 
        if db.foi_respondido_msg(msg):
            print(f"CHECK_VIDEO: pedido por {pedinte[0]} do vídeo '{msg.get_dados()}' já foi respondido")
            return
        db.add_pedido_respondido_msg(msg) #> regista o pedido para não responder novamente no futuro
        video = msg.get_dados()
        print(f"CHECK_VIDEO: pedido por {pedinte[0]} do vídeo '{video}', original do {msg.get_origem()}")
        if db.is_streaming_video(video): #> o nodo está já a transmitir o vídeo => Tem o vídeo
            print(f"CHECK_VIDEO: tenho o vídeo '{video}'")
            response = Mensagem(Mensagem.resp_check_video, dados=True, origem=sckt.getsockname()[0]) #> indica na mensagem que possui o video pretendido e indica o seu ip para quem receber saber onde ele está
            sckt.sendto(response.serialize(), pedinte) #> envia a resposta
        else: #> o nodo ainda não está a transmitir o video => não tem o vídeo
            print(f"CHECK_VIDEO: não tenho o vídeo '{video}' => broadcast para os meus vizinhos")
            vizinhos = db.get_vizinhos_for_broadcast(pedinte[0]) #> lista de vizinhos (excepto o remetente) onde ele vai efectuar um pedido de check video para descobrir onde está o vídeo
            msg_para_vizinhos = msg.serialize() #> para pedir o check video aos vizinhos (reaproveita a mensagem do cliente para manter o ID)
            vizinhos_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #> este socket serve apenas para ele perguntar aos vizinhos se eles têm o vídeo 
            vizinhos_socket.settimeout(4) #> Se o vizinho não encontrar o vídeo ele não responde, pelo que temos de definir um tempo máximo de espera. Se ultrapassar esse tempo, assumimos que o vizinho não encontrou nada.

            # Check video aos vizinhos
            for vizinho in vizinhos:
                vizinho = (vizinho,V_CHECK_PORT)
                vizinhos_socket.sendto(msg_para_vizinhos, vizinho) #> faz um check_video ao vizinho
            
            #> Recepção das respostas dos vizinhos
            try:
                resp_vizinho, addr_vizinho = vizinhos_socket.recvfrom(1024) #> vizinho responde a indicar quem tem o vídeo
                resp_vizinho = Mensagem.deserialize(resp_vizinho) #> resposta do vizinho
                db.add_route(resp_vizinho.get_origem(),addr_vizinho[0])
                print(f"CHECK_VIDEO: Confirmação da existência do '{video}' de {addr_vizinho[0]}, original do {resp_vizinho.get_origem()}")
                if resp_vizinho.get_dados(): #> o vizinho tem o vídeo
                    sckt.sendto(resp_vizinho.serialize(), pedinte) #> envia a resposta do vizinho com as informações necessárias
                else:
                    print(f"CHECK_VIDEO: Algo ocorreu de errado com a resposta de {addr_vizinho[0]}")
            except socket.timeout:
                print(f"CHECK_VIDEO: No answers from {vizinho[0]} about '{video}' asked by {pedinte[0]} ")
            
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

##################################################################################################################
#* Serviço de START_VIDEO

def handle_start_video(msg, str_sckt, addr:tuple, db: Database):
    msg = Mensagem.deserialize(msg)

    tipo = msg.get_tipo()
    pedido_id = msg.get_id()
    cliente_origem = msg.get_origem()
    from_node = addr[0]
    dados = msg.get_dados() #{'destino': ip de quem tem o vídeo, 'video': nome do vídeo}
    video = dados['video']
    ip_destino = dados['destino']

    if tipo == Mensagem.start_video:
        print(f"START_VIDEO: pedido por {addr[0]}, video '{video}', original do {cliente_origem}")
        if db.is_streaming_video(video): #> Já está a transmitir o vídeo
            print(f"START_VIDEO: O vídeo '{video}' já está a ser transmitido")
            db.add_streaming(video, addr) #> Regista o cliente/nodo que está a receber o vídeo
            print(f"START_VIDEO: {addr[0]} adicionado à lista de transmissão do vídeo '{video}', para o Cliente {cliente_origem}")
            
        else: #> Ainda não está a transmitir o vídeo
            #! Talvez ter atenção algum caso em que não haja vizinho para o destino especificado (apesar de ser teoricamente impossível)
            destino_vizinho = db.resolve_ip_to_vizinho(ip_destino) #> Resolve o ip do destino para o ip do vizinho que tem o vídeo
            start_video_msg = Mensagem(Mensagem.start_video, dados=dados) 
            str_sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            str_sckt.settimeout(5)
            print(f"START_VIDEO: A redirecionar o pedido do vídeo '{video}' para {destino_vizinho}")
            str_sckt.sendto(start_video_msg.serialize(), (destino_vizinho, V_START_PORT))
            db.add_streaming(video, addr) #! Ter atenção que pode haver um curto espaço temporal em que é dito que há streaming de um determinado vídeo mas ainda não ter começado (mt improvavel, mas...)
            relay_video(str_sckt, video, destino_vizinho, db)

    else:
        print(f"\n\nPORTA ERRADA A RECEBER PEDIDO DE {tipo} INCORRETAMENTE\nSUPOSTO RECEBER START_VIDEOS!!!!!\n\n")

def relay_video(str_sckt, video, server: str, db: Database):
    print(f"START_VIDEO: Starting relay_video for video '{video}'")
    while True:
        clients = db.get_clients_streaming(video) # clientes/dispositivos que querem ver o vídeo
        if len(clients) > 0: # ainda existem clientes a querer ver o vídeo?
            packet, _ = str_sckt.recvfrom(20480) #! Talvez fazer aqui aquela função que abstrai a recepção de packets/frames em que usa o serviço ALIVE para o tratamento de erros/falhas.
            for dest in clients: # envia o frame recebido do servidor para todos os dispositivos a ver o vídeo
                str_sckt.sendto(packet, dest)
        else: # não existem mais dispositivos a querer ver o vídeo
            break # pára a stream
        
    stop_video_msg = Mensagem(Mensagem.stop_video, dados=video).serialize()
    str_sckt.sendto(stop_video_msg, (server, V_STOP_PORT))
    str_sckt.close() 
    print(f"START_VIDEO: Streaming de '{video}' terminada")

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
##################################################################################################################

#* Serviço de STOP_VIDEO

def handle_stop_video(msg, str_sckt, addr:tuple, db: Database):
    print(f"STOP_VIDEO: Conversação estabelecida com {addr[0]}")
    msg = Mensagem.deserialize(msg)

    tipo = msg.get_tipo()
    video = msg.get_dados()

    if tipo == Mensagem.stop_video:
        print(f"STOP_VIDEO: Parei de transmitir o vídeo '{video}' para {addr[0]}")
        db.remove_streaming(video, addr)
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

    # Cria a base de dados
    db = Database()

    # Regista o sinal para encerrar o servidor no momento do CTRL+C
    signal.signal(signal.SIGINT, partial(ctrlc_handler, db))
    
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <config_file.json>")
        sys.exit(1)
    db.read_config_file(sys.argv[1])

    # Inicia o serviço de notificação de vizinhos
    svc_notify_vizinhos(db)

    # Inicia os serviços em threads separadas
    svc1_thread = threading.Thread(target=svc_check_video, args=(db,))
    svc2_thread = threading.Thread(target=svc_start_video, args=(db,))
    svc3_thread = threading.Thread(target=svc_stop_video, args=(db,))
    svc4_thread = threading.Thread(target=svc_clear_pedidos_resp, args=(db,))
    svc5_thread = threading.Thread(target=svc_add_vizinhos, args=(db,))
    svc6_thread = threading.Thread(target=svc_remove_vizinhos, args=(db,))
    svc51_thread = threading.Thread(target=svc_show_db, args=(db,))

    threads=[   
        svc1_thread,
        svc2_thread,
        svc3_thread,
        svc4_thread,
        svc5_thread,
        svc6_thread,
        svc51_thread,
    ]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()