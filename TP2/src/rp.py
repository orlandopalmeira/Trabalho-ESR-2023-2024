import socket
import threading
import signal
import sys
import time
import datetime
from Databases.database_rp import Database_RP
from aux.mensagem import Mensagem
from aux.utils import get_ips, change_terminal_title
from queue import Queue

V_CHECK_PORT = 3001 #> Porta de atendimento do serviço check_videos
V_START_PORT = 3002 #> Porta de atendimento do serviço start_videos
V_STOP_PORT  = 3003 #> Porta de atendimento do serviço stop_videos
ADD_VIZINHO_PORT= 3005 #> Porta de atendimento do serviço add_vizinho
RMV_VIZINHO_PORT= 3006 #> Porta de atendimento do serviço rmv_vizinho
ALIVE_RECEPTOR_PORT = 3007 #> Porta de atendimento do serviço alive_forn
METRICS_PORT = 3010 #> Porta para solicitar a métrica ao Servidor

# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(sig, frame):
    print("A encerrar o servidor e as threads...")
    sys.exit(0)

def thread_for_each_interface(endereço, porta, function, db: Database_RP):
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
#* SERVIÇO CHECK_VIDEOS

def handle_check_video(msg: bytes, sckt, addr:tuple, db: Database_RP):
    msg = Mensagem.deserialize(msg)
    tipo = msg.get_tipo()
    cliente_origem = msg.get_origem()
    from_node = addr[0]
    video = msg.get_dados()

    if tipo == Mensagem.CHECK_VIDEO:
        print(f"CHECK_VIDEO: pedido por {addr[0]} do vídeo '{msg.get_dados()}'{f', original do {cliente_origem}' if cliente_origem else ''}")
        if db.foi_respondido_msg(msg):
            print(f"CHECK_VIDEO: Pedido do vizinho {addr[0]} já foi respondido. Pedido ignorado.")
            return
        
        # Gestão de pedidos repetidos
        db.add_pedido_respondido_msg(msg)

        # Resposta ao pedido
        if db.servers_have_video(video):
            print(f"CHECK_VIDEO: tenho o vídeo {video}")
            origem = sckt.getsockname()[0]
            msg = Mensagem(Mensagem.RESP_CHECK_VIDEO, dados=True, origem=origem)
            sckt.sendto(msg.serialize(), addr)
        else:
            print("CHECK_VIDEO: Não existe o filme pedido na rede overlay")
            pass # Ignora o pedido

        print(f"CHECK_VIDEO: Conversação encerrada com {addr[0]}")

def svc_check_video(db: Database_RP):
    service_name = "svc_check_video"
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {V_CHECK_PORT}")
    interfaces = get_ips()
    threads = []
    for ip in interfaces:
        t = threading.Thread(target=thread_for_each_interface, args=(ip, V_CHECK_PORT, handle_check_video, db))
        t.daemon = True
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()

##################################################################################################################
#* SERVIÇO START_VIDEOS

def handle_start_video(msg: bytes, sckt, addr:tuple, db: Database_RP):
    msg = Mensagem.deserialize(msg)

    video = msg.get_dados()['video'] #> Nome do vídeo que o remetente pretende ver 

    print(f"START_VIDEO recebido de {addr[0]} pedindo o video '{video}'")
    if db.servers_have_video(video): #> O RP verifica a existência do vídeo na overlay
        if db.is_streaming_video(video): #> O RP verifica se o vídeo já está a ser transmitido
            print(f"START_VIDEO: O vídeo '{video}' já está a ser transmitido")
            db.add_streaming(video, addr) #> Regista o cliente/nodo como um "visualizador" do vídeo
            
        else: #> Ainda não está a receber o vídeo
            best_server = db.get_best_server(video) #> Vai buscar o vídeo ao melhor servidor
            print(f"START_VIDEO: não estou a transmitir o vídeo '{video}' => solicitação ao servidor {best_server}")
            start_video_msg = Mensagem(Mensagem.START_VIDEO, dados=video) #> Mensagem de soliticação do vídeo ao servidor
            sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #> Socket para comunicar com o servidor
            sckt.settimeout(5)
            sckt.sendto(start_video_msg.serialize(), (best_server, V_START_PORT)) #> Envia a mensagem de soliticação do vídeo para o servidor
            db.add_streaming(video, addr) #> Regista o cliente/nodo como um "visualizador" do vídeo
            print(f"START_VIDEO: Transmissão do vídeo '{video}' iniciada")
            relay_video(sckt, video, best_server, db) #> Inicia o envio do vídeo para os clientes/nodos
    else:
        print(f"START_VIDEO: O vídeo '{video}' não existe na rede overlay. Pedido ignorado.")
        
def relay_video(str_sckt, video, server: str, db: Database_RP):
    while True:
        clients = db.get_clients_streaming(video) # clientes/dispositivos que querem ver o vídeo
        if len(clients) > 0: # ainda existem clientes a querer ver o vídeo?
            packet, _ = str_sckt.recvfrom(20480) 
            for dest in clients: # envia o frame recebido do servidor para todos os dispositivos a ver o vídeo
                str_sckt.sendto(packet, dest)
        else: # não existem mais dispositivos a querer ver o vídeo
            break # pára a stream
        
    stop_video_msg = Mensagem(Mensagem.STOP_VIDEO, dados=video).serialize()
    str_sckt.sendto(stop_video_msg, (server, V_STOP_PORT))
    str_sckt.close() 
    print(f"Streaming de '{video}' terminada")

def svc_start_video(db: Database_RP):
    service_name = "svc_start_video"
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {V_START_PORT}")
    interfaces = get_ips()
    threads = []
    for ip in interfaces:
        t = threading.Thread(target=thread_for_each_interface, args=(ip, V_START_PORT, handle_start_video, db))
        t.daemon = True
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()

##################################################################################################################
#* SERVIÇO STOP_VIDEOS

def handle_stop_video(msg: bytes, sckt, addr:tuple, db: Database_RP):
    msg = Mensagem.deserialize(msg)
    video = msg.get_dados()
    db.remove_streaming(video, addr)

def svc_stop_video(db: Database_RP):
    service_name = "svc_stop_video"
    print(f"Serviço '{service_name}' pronto para receber conexões na porta {V_STOP_PORT}")
    interfaces = get_ips()
    threads = []
    for ip in interfaces:
        t = threading.Thread(target=thread_for_each_interface, args=(ip, V_STOP_PORT, handle_stop_video, db))
        t.daemon = True
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()

##################################################################################################################
#* Solicitar a lista dos vídeos nos servidores

# Pede a um servidor os seus videos
def handler_get_videos_from_server(server_ip: str, db: Database_RP):
    """Pede a um servidor todos os seus vídeos"""
    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sckt.settimeout(6)
        server = (server_ip,V_CHECK_PORT)
        msg = Mensagem(Mensagem.CHECK_VIDEO).serialize()
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
        time.sleep(120)

##################################################################################################################
#* Metricas 

# Pede a um servidor os seus videos
def handler_measure_metrics(server_ip: str, db: Database_RP):
    """Pede a um servidor todos os seus vídeos"""
    print(f"A medir métrica do servidor {server_ip}")
    num_of_requests = 10
    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sckt.settimeout(5)
        server = (server_ip, METRICS_PORT)
        for i in range(num_of_requests):
            msg = Mensagem(Mensagem.METRICA).serialize()
            sckt.sendto(msg, server)
            # print(f"Enviada mensagem de teste {i} para o servidor {server}")
        # print(f"Enviadas {num_of_requests} mensagens de métrica para o servidor {server}")  

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
            avg_delivery_time = round(avg_delivery_time, 10)
            final_metric = 0.5 * (1 / avg_delivery_time) + 0.5 * (successes/num_of_requests) # Quanto maior a métrica, melhor
            # final_metric = (1 - (avg_delivery_time / "Max Tolerable Delay Time")) * ((successes/num_of_requests) * 100)
            final_metric = round(final_metric, 4)
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
    TIME_BETWEEN_METRIC_MESSAGES = 120 # em secs
    while True:
        svc_measure_metrics(db)
        time.sleep(TIME_BETWEEN_METRIC_MESSAGES) 

##################################################################################################################
#* Serviço de ADD_VIZINHOS
# Função para lidar com o serviço svc_add_vizinhos
def handle_add_vizinhos(msg, socket, addr:tuple, db: Database_RP):
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
def svc_add_vizinhos(db: Database_RP):
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
def handle_remove_vizinhos(msg, addr:tuple, db: Database_RP):
    print(f"REMOVE_VIZINHO: recebido de {addr[0]}")
    msg = Mensagem.deserialize(msg)
    if not msg.get_tipo() == Mensagem.RMV_VIZINHO: # mensagem será de tipo diferente
        print(f"REMOVE_VIZINHO: pedido de {addr[0]} não é do tipo RMV_VIZINHO")
        return
    
    r = db.remove_vizinho(addr[0])
    if r == 1:
        print(f"REMOVE_VIZINHO: {addr[0]} NÃO EXISTIA na lista de vizinhos!!!!!")
    else:
        print(f"REMOVE_VIZINHO: {addr[0]} removido dos vizinhos com sucesso.")

# Função que lida com o serviço de adicionar vizinhos
def svc_remove_vizinhos(db: Database_RP):
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

#* Serviço que limpa os pedidos respondidos da base de dados
def svc_clear_pedidos_resp(db: Database_RP):
    service_name = 'svc_clear_pedidos_resp'
    interval = 15
    max_age_secs = 10
    print(f"Serviço '{service_name}' a limpar pedidos já respondidos há mais de {max_age_secs} de {interval} em {interval} segundos.")
    while True:
        db.remove_pedidos_respondidos(max_age_secs)
        time.sleep(interval)

##################################################################################################################

#? Para debug, que mostra o conteúdo da base de dados
def svc_show_db(db: Database_RP):
    while True:
        print("-"*20); print(db); print("-"*20)
        time.sleep(25)

##################################################################################################################

#* Serviço relativos à receção de ALIVE_RECEPTOR's

def svc_recv_alive_receptor(db: Database_RP):
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


def handle_recv_alive_receptor(msg, addr:tuple, db: Database_RP):
    """ Handler do svc de receção de ALIVE_RECEPTOR's"""
    msg = Mensagem.deserialize(msg)
    if msg.get_tipo() == Mensagem.ALIVE_RECEPTOR:
        db.update_aliveness_of_receptor(addr[0])
        print(f"ALIVE_RECEPTOR: {addr[0]} atualizado.")
    else:
        print(f"ALIVE_RECEPTOR: pedido de {addr[0]} não é do tipo ALIVE_RECEPTOR")


def svc_treat_dead_receptors(db: Database_RP):
    """ Serviço que trata de remover os fornecedores que não estão ativos"""
    service_name = 'svc_treat_dead_receptors'
    interval = 40
    max_age_secs = 60 # Com o envio de 20 em 20 segundos, se um fornecedor não responder em 60 segundos, é considerado morto
    print(f"Serviço '{service_name}' a tratar de fornecedores inativos de {interval} em {interval} segundos.")
    while True:
        db.treat_dead_receptors(max_age_secs)
        time.sleep(interval)


##################################################################################################################


def main():
    change_terminal_title()
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
    svc1_thread = threading.Thread(target=svc_check_video, args=(db,))
    svc2_thread = threading.Thread(target=svc_stop_video, args=(db,))
    svc3_thread = threading.Thread(target=svc_start_video, args=(db,))
    svc4_thread = threading.Thread(target=svc_measure_metrics_continuous, args=(db,))
    svc5_thread = threading.Thread(target=svc_add_vizinhos, args=(db,))
    svc6_thread = threading.Thread(target=svc_remove_vizinhos, args=(db,))

    svc7_thread = threading.Thread(target=svc_recv_alive_receptor, args=(db,))
    svc9_thread = threading.Thread(target=svc_treat_dead_receptors, args=(db,))

    svc_clear_ans_reqs = threading.Thread(target=svc_clear_pedidos_resp, args=(db,))

    show_db_thread = threading.Thread(target=svc_show_db, args=(db,))

    threads = [
        svc1_thread,
        svc2_thread, 
        svc3_thread,
        svc4_thread,
        svc5_thread,
        svc6_thread,
        svc_clear_ans_reqs,
        svc7_thread,
        svc9_thread,
        # show_db_thread,
    ]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()