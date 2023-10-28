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
#! WIP
# Verifica se tem o filme pedido e adiciona o cliente à sua routingTable
def handle_check_video(msg, socket, addr:tuple, db: Database):
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
def svc_check_video(port:int, db: Database):
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

def main():

    db = Database()
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <config_file.json>")
        sys.exit(1)
    db.read_config_file(sys.argv[1])

    # Regista o sinal para encerrar o servidor no momento do CTRL+C
    signal.signal(signal.SIGINT, ctrlc_handler)

    # Inicia os serviços em threads separadas
    svc1_thread = threading.Thread(target=svc_attend_clients, args=(3000, db))
    svc2_thread = threading.Thread(target=svc_add_vizinhos, args=(3001, db))
    svc3_thread = threading.Thread(target=svc_remove_vizinhos, args=(3002, db))
    svc4_thread = threading.Thread(target=svc_check_video, args=(3003, db))
    svc5_thread = threading.Thread(target=svc_show_vizinhos, args=(db,))

    threads = [svc1_thread, svc2_thread, svc3_thread, svc4_thread, svc5_thread]

    for t in threads:
        t.daemon = True
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()