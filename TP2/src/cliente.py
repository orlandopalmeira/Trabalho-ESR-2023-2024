import sys
import socket
import json
from tkinter import Tk
from aux.ClienteGUI import ClienteGUI

from aux.mensagem import Mensagem
from aux.utils import get_ips, change_terminal_title

V_CHECK_PORT = 3001 #> Porta de atendimento do serviço check_videos
V_START_PORT = 3002 #> Porta de atendimento do serviço start_videos
V_STOP_PORT  = 3003 #> Porta de atendimento do serviço stop_videos

if __name__ == "__main__":
	root = Tk()
	change_terminal_title()
	my_name = socket.gethostname()

	#* Verificação dos argumentos
	if len(sys.argv) < 3:
		print("Uso: python3 cliente.py <config_file.json> <video>")
		sys.exit(1)
	with open(sys.argv[1]) as f:
		config = json.load(f)

	#* Configuração do cliente 
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
	msg = Mensagem(Mensagem.CHECK_VIDEO, dados=video, origem=self_ip)
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
	destino = msg.get_origem()
	msg = Mensagem(Mensagem.START_VIDEO, dados={'destino': destino, 'video': video}, origem=self_ip)
	print(f"Pedido de vídeo: {msg}")
	msg = msg.serialize()
	sckt.sendto(msg, dest_start)
	try:
		#! Verificar timeouts e assim la dentro do clienteGUI
		# Create a new client
		app = ClienteGUI(root, sckt)
		app.master.title(f"{my_name}({self_ip}) - {video} from {destino}") 
		root.mainloop()
	finally:
		print("A terminar vídeo...")
		stop_video_msg = Mensagem(Mensagem.STOP_VIDEO, dados=video).serialize()
		sckt.sendto(stop_video_msg, dest_stop)
	