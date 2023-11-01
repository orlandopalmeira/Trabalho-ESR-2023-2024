import sys
import socket
import json
from tkinter import Tk
sys.path.append("./Python")
from ClienteGUI import ClienteGUI

from database import Database
from mensagem import Mensagem

if __name__ == "__main__":
	root = Tk()

	#* Verificação dos argumentos
	if len(sys.argv) < 3:
		print("Uso: python3 cliente.py <config_file.json> <video>")
		sys.exit(1)
	with open(sys.argv[1]) as f:
		config = json.load(f)

	#* Configuração do cliente
	self_ip = config["self_ip"]
	dest_addr = config["vizinho"]
	dest_port = 3000
	video = sys.argv[2]

	print(f"A enviar pedido apenas para o servidor {dest_addr}:{dest_port}")
	print(f"A pedir o video {video}")
	
	dest = (dest_addr, dest_port)
	sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# Se não receber resposta em 5 segundos, assume que a rede overlay não tem o vídeo
	sckt.settimeout(5)


	#* Verificação da existencia do video
	msg = Mensagem(Mensagem.check_video, dados=video, origem=self_ip)
	msg = msg.serialize()
	sckt.sendto(msg, dest)
	try:
		msg, addr = sckt.recvfrom(1024)
	except socket.timeout:
		print(f"Timeout ao receber resposta CHECK_VIDEO do video {video}")
		print("Assumido que o vídeo não existe na rede overlay")
		print("A sair...")
		sys.exit(1)
	msg = Mensagem.deserialize(msg)
	print("Reposta a CHECK_VIDEO:")
	print(msg)


	msg = Mensagem(Mensagem.start_video, dados="movie.Mjpeg", origem=self_ip)
	msg = msg.serialize()
	sckt.sendto(msg, dest)
	#! Verificar timeouts e assim la dentro do clienteGUI
	# Create a new client
	# app = ClienteGUI(root, addr, port)
	app = ClienteGUI(root, sckt)
	app.master.title("Cliente Exemplo")	
	root.mainloop()
	
