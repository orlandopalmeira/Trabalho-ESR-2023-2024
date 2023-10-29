import sys
from tkinter import Tk
from ClienteGUI import ClienteGUI


if __name__ == "__main__":
	root = Tk()

	addr = "0.0.0.0"
	port = 25000
	
	# Create a new client
	app = ClienteGUI(root, addr, port)
	app.master.title("Cliente Exemplo")	
	root.mainloop()
	
