import socket
import threading
import signal
import sys
import time
from Databases.database import Database
from aux.mensagem import Mensagem
from aux.utils import get_ips, change_terminal_title
from functools import partial

V_CHECK_PORT = 3001 #> Porta de atendimento do serviço check_videos
V_START_PORT = 3002 #> Porta de atendimento do serviço start_videos
V_STOP_PORT  = 3003 #> Porta de atendimento do serviço stop_videos
ADD_VIZINHO_PORT= 3005 #> Porta de atendimento do serviço add_vizinho
RMV_VIZINHO_PORT= 3006 #> Porta de atendimento do serviço rmv_vizinho
ALIVE_RECEPTOR_PORT = 3007 #> Porta de atendimento do serviço alive_receptor


# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(db: Database, sig, frame):
    print("A encerrar o servidor e as threads...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = Mensagem(Mensagem.RMV_VIZINHO)
    msg = msg.serialize()
    for v in db.get_vizinhos():
        s.sendto(msg, (v, RMV_VIZINHO_PORT))
        print(f"Enviado pedido de remoção de vizinho para {v}")
    s.close()
    sys.exit(0)

# Função para encerrar repentinamente no momento do CTRL+P
def ctrl_slash_handler(sig, frame):
    print("A simular encerramento repentino...")
    sys.exit(0)


def thread_for_each_interface(endereço, porta, function, db: Database):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((endereço, porta))
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
    msg = Mensagem(Mensagem.ADD_VIZINHO).serialize()
    sckt.sendto(msg, vizinho)
    try:
        resp, _ = sckt.recvfrom(2048)
        resp = Mensagem.deserialize(resp)
        if resp.get_tipo() == Mensagem.ADD_VIZINHO:
            print(f"Vizinho {vizinho[0]} notificado com sucesso.")
        else:
            print(f"Vizinho {vizinho[0]} NÃO respondeu com o tipo ADD_VIZINHO!!!")
        sckt.close()
    except socket.timeout:
        # print(f"Timeout {vizinho[0]} DEBUG")
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
    threads = []

    for v in vizinhos_addr:
        sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sckt.settimeout(2)
        t=threading.Thread(target=handle_notify_vizinhos, args=(v,sckt))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

##################################################################################################################
#* Serviço de ADD_VIZINHOS
# Função para lidar com o serviço svc_add_vizinhos
def handle_add_vizinhos(msg, socket, addr:tuple, db: Database):
    print(f"ADD_VIZINHO: recebido de {addr[0]}")
    msg = Mensagem.deserialize(msg)
    if not msg.get_tipo() == Mensagem.ADD_VIZINHO:
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
    if not msg.get_tipo() == Mensagem.RMV_VIZINHO:
        print(f"REMOVE_VIZINHO: pedido de {addr[0]} não é do tipo RMV_VIZINHO")
        return
    
    r = db.remove_vizinho(addr[0])
    if r == 1:
        print(f"REMOVE_VIZINHO: {addr[0]} NÃO EXISTIA na lista de vizinhos!!!!!")
    else:
        print(f"REMOVE_VIZINHO: {addr[0]} removido dos vizinhos com sucesso.")

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
    interval = 40
    print(f"Serviço '{service_name}' pronto para mostrar a db de {interval} em {interval} segundos. (DEBUG)")
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

#* Serviço relativos ao envio e receção de ALIVE_RECEPTOR's

def svc_send_alive_receptor(db: Database):
    """Serviço que envia ALIVE_RECEPTOR's para os fornecedores de X em X segundos; X = 30"""
    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = Mensagem(Mensagem.ALIVE_RECEPTOR).serialize()
    interval = 20
    print(f"Serviço 'svc_send_alive_receptor' a enviar ALIVE_RECEPTOR's para os fornecedores de {interval} em {interval} segundos.")
    while True:
        try:
            fornecedores = db.get_fornecedores()
            for f in fornecedores:
                sckt.sendto(msg, (f, ALIVE_RECEPTOR_PORT))
                # Não precisa de nenhum ACK, porque se o fornecedor não estiver ativo isso é descoberto através de timeouts
            time.sleep(interval)
        except Exception as e:
            print(f"Erro svc_send_alive_receptor: {e}")
            break
    sckt.close()

def svc_recv_alive_receptor(db: Database):
    """ Serviço que recebe ALIVE_RECEPTOR's e regista o sinal de vida dos fornecedores"""
    service_name = 'svc_recv_alive_receptor'
    print(f"Serviço '{service_name}' pronto para receber ALIVE_RECEPTOR's na porta {ALIVE_RECEPTOR_PORT}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', ALIVE_RECEPTOR_PORT))
    while True:
        try:
            dados, addr = server_socket.recvfrom(1024)
            threading.Thread(target=handle_recv_alive_receptor, args=(dados, addr, db)).start()
        except Exception as e:
            print(f"Erro svc_alive_receptor: {e}")
            break
    server_socket.close()


def handle_recv_alive_receptor(msg, addr:tuple, db: Database):
    """ Handler do svc de receção de ALIVE_RECEPTOR's"""
    msg = Mensagem.deserialize(msg)
    if msg.get_tipo() == Mensagem.ALIVE_RECEPTOR:
        db.update_aliveness_of_receptor(addr[0])
        print(f"ALIVE_RECEPTOR: {addr[0]} atualizado.")
    else:
        print(f"ALIVE_RECEPTOR: pedido de {addr[0]} não é do tipo ALIVE_RECEPTOR")


def svc_treat_dead_receptors(db: Database):
    """ Serviço que trata de remover os fornecedores que não estão ativos"""
    service_name = 'svc_treat_dead_receptors'
    interval = 40
    max_age_secs = 60 # Com o envio de 20 em 20 segundos, se um fornecedor não responder em 60 segundos, é considerado morto
    print(f"Serviço '{service_name}' a tratar de fornecedores inativos de {interval} em {interval} segundos.")
    while True:
        db.treat_dead_receptors(max_age_secs)
        time.sleep(interval)



##################################################################################################################
#* Serviço de CHECK_VIDEO
def handle_check_video(data: bytes, sckt, pedinte: tuple, db: Database):
    msg = Mensagem.deserialize(data)
    tipo = msg.get_tipo()
    if tipo == Mensagem.CHECK_VIDEO: #> para evitar responder a pedidos que não sejam deste tipo 
        if db.foi_respondido_msg(msg):
            print(f"CHECK_VIDEO: pedido por {pedinte[0]} do vídeo '{msg.get_dados()}' já foi respondido")
            return
        db.add_pedido_respondido_msg(msg) #> regista o pedido para não responder novamente no futuro
        video = msg.get_dados()
        print(f"CHECK_VIDEO: pedido por {pedinte[0]} do vídeo '{video}'{f', original do {msg.get_origem()}' if msg.get_origem() else ''}")
        if db.is_streaming_video(video): #> o nodo está já a transmitir o vídeo => Tem o vídeo
            print(f"CHECK_VIDEO: tenho o vídeo '{video}'")
            response = Mensagem(Mensagem.RESP_CHECK_VIDEO, dados=True, origem=sckt.getsockname()[0]) #> indica na mensagem que possui o video pretendido e indica o seu ip para quem receber saber onde ele está
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
                print(f"CHECK_VIDEO: Confirmação da existência do '{video}' de {addr_vizinho[0]}{f', original do {msg.get_origem()}' if msg.get_origem() else ''}")
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
    cliente_origem = msg.get_origem()
    dados = msg.get_dados() # {'destino': ip de quem tem o vídeo, 'video': nome do vídeo}
    video = dados['video']
    ip_destino = dados['destino']

    if not tipo == Mensagem.START_VIDEO:
        print(f"\n\nPORTA ERRADA A RECEBER PEDIDO DE {tipo} INCORRETAMENTE\nSUPOSTO RECEBER START_VIDEOS!!!!!\n\n")
        return 

    print(f"START_VIDEO: pedido por {addr[0]}, video '{video}'{f', original do {cliente_origem}' if cliente_origem else ''}") 
    if db.is_streaming_video(video): #> Já está a transmitir o vídeo
        print(f"START_VIDEO: O vídeo '{video}' já está a ser transmitido")
        db.add_streaming(video, addr) #> Regista o cliente/nodo que está a receber o vídeo
        print(f"START_VIDEO: {addr[0]} adicionado à lista de transmissão do vídeo '{video}'{f', para o Cliente {cliente_origem}' if cliente_origem else ''}")
        
    else: #> Ainda não está a transmitir o vídeo
        destino_vizinho = db.resolve_ip_to_vizinho(ip_destino) #> Resolve o ip do destino para o ip do vizinho que tem o vídeo
        start_video_msg = Mensagem(Mensagem.START_VIDEO, dados=dados) 
        str_sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"START_VIDEO: A redirecionar o pedido do vídeo '{video}' para {destino_vizinho}")
        str_sckt.sendto(start_video_msg.serialize(), (destino_vizinho, V_START_PORT))
        db.add_streaming(video, addr) #> Adiciona o par video:addr de envio
        db.add_streaming_from(destino_vizinho, video) #> Adiciona o par ip_fornecedor:video 
        relay_video(str_sckt, video, destino_vizinho, db)

def relay_video(str_sckt, video:str, fornecedor:str, db: Database):
    """ Função que recebe um determinado vídeo e reencaminha o vídeo para os cliente que o pedem.
        Ela gere a lógica de parar a stream quando não existem mais clientes a querer ver o vídeo e também de arranjar uma nova rota caso o fornecedor do vídeo falhe."""
    print(f"START_VIDEO: Starting relay_video for video '{video}'")
    str_sckt.settimeout(1) # Timeout de 1 segundo, para verificar se o proveniente está vivo
    retries = 0
    oldPacket = None
    packet = None
    while True:
        clients = db.get_clients_streaming(video) # clientes/dispositivos que querem ver o vídeo
        if len(clients) > 0: # ainda existem clientes a querer ver o vídeo?
            try:
                oldPacket = packet
                packet, addr, retries = receive_video_frame(str_sckt, fornecedor, video, db, retries=retries)
                if not packet: #> Se o packet for None, é porque houve algum timeout e queremos enviar o último frame que recebemos como dummy packet
                    print(f"Enviado um dummy packet, devido a falta do fornecedor {fornecedor} do vídeo '{video}'")
                    packet = oldPacket # dummy packet
            except: # Caso não haja nenhum fornecedor a fornecer o vídeo
                print(f"Não foram encontrados fornecedores para o video '{video}' após um rearranjo!!!")
                break
            fornecedor = addr[0] #> Atualiza o fornecedor do vídeo, para o caso de ter mudado
            for dest in clients: # envia o frame recebido do servidor para todos os dispositivos a ver o vídeo
                str_sckt.sendto(packet, dest)
        else: # não existem mais dispositivos a querer ver o vídeo
            break # pára a stream
    
    db.remove_streaming_from(fornecedor, video)
    # Não tem de se fazer db.remove_streaming, pois isso já foi feito no handle_stop_video, que pode causar a paragem deste ciclo, se remover todos os destinos que querem o video que está a receber.
    stop_video_msg = Mensagem(Mensagem.STOP_VIDEO, dados=video).serialize()
    str_sckt.sendto(stop_video_msg, (fornecedor, V_STOP_PORT))
    str_sckt.close() 
    print(f"START_VIDEO: Streaming de '{video}' terminada")


def receive_video_frame(sckt, ip_fornecedor:str, video:str, db: Database, retries=0):
    """ Abstrai logica de recepção de frames/packets para o relay_video e a sua forma de lidar com erros/falhas
        Pode retornar um addr, diferente do fornecedor original, sendo necessário atualizar o fornecedor do vídeo"""
    try:
        packet, addr = sckt.recvfrom(20480)
    except socket.timeout:
        if not db.is_transmitting_video(ip_fornecedor): ## Caso em que o nodo fornecedor mandou um RMV_VIZINHO
            print(f"START_VIDEO: {ip_fornecedor} deixou de estar ativo para fornecer o video '{video}'")
            print(f"START_VIDEO: A procurar um novo fornecedor para o vídeo '{video}'")
            new_fornecedor = rearranje_fornecedor(sckt, video, db)
            # packet, addr = sckt.recvfrom(20480)
            packet, addr, retries = receive_video_frame(sckt, new_fornecedor, video, db)
            print(f"START_VIDEO: Novo fornecedor para o vídeo '{video}' encontrado: {new_fornecedor}")

        else: #> O fornecedor ainda está ativo, mas não está a enviar o vídeo (potencial falha abrupta)
            if retries > 2:
                print(f"START_VIDEO: {ip_fornecedor} ultrapassou o limite de falhas de fornecimento do video '{video}'")
                db.remove_streaming_from(ip_fornecedor, video) # Aqui é necessário remover do streaming_from pois n recebeu nenhum RMV_VIZINHO, mas vai-se rearranjar de fornecedor.
                new_fornecedor = rearranje_fornecedor(sckt, video, db)
                print(f"START_VIDEO: Novo fornecedor para o vídeo '{video}' encontrado: {new_fornecedor}")
                packet, addr, retries = receive_video_frame(sckt, new_fornecedor, video, db)
                
            else:
                print(f"START_VIDEO: {ip_fornecedor} deu um timeout no envio do vídeo '{video}'. Retries: {retries+1}")
                ##? Mandar mensagem dummy rtp packet para que não despolete timeouts nos nodos prévios.
                packet = None ## Significa envio de dummy packet
                addr = (ip_fornecedor, V_START_PORT)
                retries += 1
                # packet, addr = receive_video_frame(sckt, ip_fornecedor, video, db, retries=retries+1)

    return packet, addr, retries

def rearranje_fornecedor(sckt, video:str, db: Database) -> str:
    """ Função que procura um novo fornecedor para o vídeo especificado, retornando o ip do novo fornecedor"""
    msg = Mensagem(Mensagem.CHECK_VIDEO, dados=video) 
            
    # Broadcast para os vizinhos de CHECK_VIDEO
    for vizinho in db.get_vizinhos():
        vizinho = (vizinho,V_CHECK_PORT)
        sckt.sendto(msg.serialize(), vizinho) 
    
    #> Recepção das respostas dos vizinhos
    sckt.settimeout(3)
    try:
        resp_vizinho, addr_vizinho_fornecedor = sckt.recvfrom(1024) #> vizinho responde a indicar quem tem o vídeo
    except socket.timeout:
        print(f"CHECK_VIDEO IN REARRANJE_FORNECEDOR: No answers from {db.get_vizinhos()} about '{video}'")
        raise Exception("Video not available")
    resp_vizinho = Mensagem.deserialize(resp_vizinho) #> resposta do vizinho
    nodo_fornecedor = resp_vizinho.get_origem()
    ip_vizinho_fornecedor = addr_vizinho_fornecedor[0]
    db.add_route(nodo_fornecedor, ip_vizinho_fornecedor)
    print(f"CHECK_VIDEO: Confirmação da existência do '{video}' de {ip_vizinho_fornecedor}, original do {nodo_fornecedor}")

    start_video_msg = Mensagem(Mensagem.START_VIDEO, dados={'video': video, 'destino': nodo_fornecedor})
    sckt.settimeout(1) 
    print(f"START_VIDEO: A redirecionar o pedido do vídeo '{video}' para {ip_vizinho_fornecedor}")
    sckt.sendto(start_video_msg.serialize(), (ip_vizinho_fornecedor, V_START_PORT))
    # db.add_streaming(video, addr) #> Não precisa do add_streaming, pois o cliente continua a querer ver o vídeo e nunca foi removida essa info
    db.add_streaming_from(ip_vizinho_fornecedor, video)

    return ip_vizinho_fornecedor


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
    msg = Mensagem.deserialize(msg)

    tipo = msg.get_tipo()
    video = msg.get_dados()

    if tipo == Mensagem.STOP_VIDEO:
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
    change_terminal_title()
    # Cria a base de dados
    db = Database()

    # Regista o sinal para encerrar o servidor no momento do CTRL+C
    signal.signal(signal.SIGINT, partial(ctrlc_handler, db))
    # Regista o sinal para simular o encerramento repentino do servidor no momento do CTRL+\
    signal.signal(signal.SIGQUIT, ctrl_slash_handler)
    
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

    svc7_thread = threading.Thread(target=svc_recv_alive_receptor, args=(db,))
    svc8_thread = threading.Thread(target=svc_send_alive_receptor, args=(db,))
    svc9_thread = threading.Thread(target=svc_treat_dead_receptors, args=(db,))
    svc_showdb_thread = threading.Thread(target=svc_show_db, args=(db,))

    threads=[   
        svc1_thread,
        svc2_thread,
        svc3_thread,
        svc4_thread,
        svc5_thread,
        svc6_thread,
        svc7_thread,
        svc8_thread,
        svc9_thread,
        # svc_showdb_thread,
    ]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()