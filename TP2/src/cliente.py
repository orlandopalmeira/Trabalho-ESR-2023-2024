import sys
import socket
import json
from tkinter import Tk
sys.path.append("./Python")
from ClienteGUI import ClienteGUI

from database import Database
from mensagem import Mensagem
from utils import get_ips

V_CHECK_PORT = 3001 #> Porta de atendimento do serviço check_videos
V_START_PORT = 3002 #> Porta de atendimento do serviço start_videos
V_STOP_PORT = 3003 #> Porta de atendimento do serviço stop_videos

if __name__ == "__main__":
	root = Tk()

	#* Verificação dos argumentos
	if len(sys.argv) < 3:
		print("Uso: python3 cliente.py <config_file.json> <video>")
		sys.exit(1)
	with open(sys.argv[1]) as f:
		config = json.load(f)

	#* Configuração do cliente 
	#! Talvez meter type check nisto para ver se é string e tal, pq me deu trabalho de identificar que estava aqui um problema
	# self_ip = config["self_ip"] # versão antiga
	self_ip = get_ips()[0] #> Obtém informação do seu próprio IP
	dest_addr = config["vizinho"]
	video = sys.argv[2]
	dest_check = (dest_addr, V_CHECK_PORT)
	dest_start = (dest_addr, V_START_PORT)
	dest_stop = (dest_addr, V_STOP_PORT)

	print(f"A enviar pedido apenas para o servidor {dest_addr}:{V_CHECK_PORT}")
	print(f"A pedir o video {video}")
	
	sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# Se não receber resposta em 5 segundos, assume que a rede overlay não tem o vídeo
	sckt.settimeout(5)


	#* Verificação da existencia do video
	msg = Mensagem(Mensagem.check_video, dados=video, origem=self_ip)
	msg = msg.serialize()
	sckt.sendto(msg, dest_check)
	try:
		msg, addr = sckt.recvfrom(1024)
	except socket.timeout:
		print(f"Timeout ao receber resposta CHECK_VIDEO do video {video}")
		print("Assumido que o vídeo não existe na rede overlay")
		print("A sair...")
		sys.exit(1)
	msg = Mensagem.deserialize(msg) #> Nesta mensagem contém o ip do nodo/rp que possui o vídeo no campo 'origem'
	print("Resposta a CHECK_VIDEO:")
	print(msg)

	#* Iniciar o vídeo
	msg = Mensagem(Mensagem.start_video, dados={'destino': msg.get_origem(), 'video': video}, origem=self_ip) #! (!VER MELHOR ISTO!) assume-se que o cliente envia nos dados da mensagem um dicionário com o formato {'destino': ip de quem tem o vídeo, 'video': nome do vídeo}
	print(f"Pedido de vídeo: {msg}")
	msg = msg.serialize()
	sckt.sendto(msg, dest_start)
	try:
		#! Verificar timeouts e assim la dentro do clienteGUI
		# Create a new client
		# app = ClienteGUI(root, addr, port)
		app = ClienteGUI(root, sckt)
		app.master.title("Cliente Exemplo")	
		root.mainloop()
	finally:
		print("A terminar vídeo...")
		stop_video_msg = Mensagem(Mensagem.stop_video, dados=video).serialize()
		sckt.sendto(stop_video_msg, dest_stop)
	