import sys, socket
from tkinter import Tk
from ClienteGUI import ClienteGUI

sys.path.append("../")

from database import Database
from mensagem import Mensagem

if __name__ == "__main__":
	root = Tk()

	# addr = "0.0.0.0"
	# port = 25000
	
	dest_addr = "10.0.4.10"
	dest_port = 3000
	dest = (dest_addr, dest_port)

	socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	msg = Mensagem(Mensagem.check_video, "dummy_ip", "movie.Mjpeg")

	msg = msg.serialize()
	socket.sendto(msg, dest)

	msg, addr = socket.recvfrom(1024)
	msg = Mensagem.deserialize(msg)
	print(msg)
	##ifs
	msg = Mensagem(Mensagem.start_video, "dummy_ip", "movie.Mjpeg")
	socket.sendto(msg.serialize(), dest)


	
	# Create a new client
	# app = ClienteGUI(root, addr, port)
	app = ClienteGUI(root, socket)
	app.master.title("Cliente Exemplo")	
	root.mainloop()
	
