import sys, socket
from tkinter import Tk
sys.path.append("./Python")
from ClienteGUI import ClienteGUI

from database import Database
from mensagem import Mensagem

if __name__ == "__main__":
	root = Tk()

	dest_addr = "10.0.4.10"
	dest_port = 3000
	# video = "movie.Mjpeg"
	video = sys.argv[1]
	# if len(sys.argv) > 1:
	# 	dest_addr = sys.argv[1]
	# if len(sys.argv) > 2:
	# 	dest_port = int(sys.argv[2]) 
	print(f"A enviar pedido apenas para o servidor {dest_addr}:{dest_port}")
	
	dest = (dest_addr, dest_port)
	socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	#* Verificação da existencia do video
	msg = Mensagem(Mensagem.check_video, "dummy_ip", video)
	msg = msg.serialize()
	socket.sendto(msg, dest)
	msg, addr = socket.recvfrom(1024)
	msg = Mensagem.deserialize(msg)
	print(msg)



	##ifs

	msg = Mensagem(Mensagem.start_video, "dummy_ip", "movie.Mjpeg")
	msg = msg.serialize()
	socket.sendto(msg, dest)


	print("aqui")
	# Create a new client
	# app = ClienteGUI(root, addr, port)
	app = ClienteGUI(root, socket)
	app.master.title("Cliente Exemplo")	
	root.mainloop()
	
