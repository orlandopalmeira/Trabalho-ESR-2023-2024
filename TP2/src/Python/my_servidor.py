from random import randint
import sys, traceback, threading, socket

from VideoStream import VideoStream
from RtpPacket import RtpPacket

sys.path.append("../")

from database import Database
from mensagem import Mensagem
import signal

class Servidor:	

	def sendRtp(self):
		"""Send RTP packets over UDP."""
		while True:
			self.clientInfo['event'].wait(0.05)
			
			# Stop sending if request is PAUSE or TEARDOWN
			if self.clientInfo['event'].isSet():
				break
				
			data = self.clientInfo['videoStream'].nextFrame()
			if data:
				frameNumber = self.clientInfo['videoStream'].frameNbr()
				try:
					address = self.clientInfo['rtpAddr']
					port = int(self.clientInfo['rtpPort'])
					packet =  self.makeRtp(data, frameNumber)
					self.clientInfo['rtpSocket'].sendto(packet,(address,port))
				except:
					print("Connection Error")
					print('-'*60)
					traceback.print_exc(file=sys.stdout)
					print('-'*60)
		# Close the RTP socket
		self.clientInfo['rtpSocket'].close()
		print("All done!")

	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0
		
		rtpPacket = RtpPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		print("Encoding RTP Packet: " + str(seqnum))
		
		return rtpPacket.getPacket()

	
	def serve_movie(self, dest_addr:str, dest_port:int, movie_name:str):

		# Para o indicar onde os filmes estão guardados
		filename = f"{movie_name}"

		self.clientInfo = dict()

		# videoStream
		self.clientInfo['videoStream'] = VideoStream(filename)
		# socket
		self.clientInfo['rtpPort'] = dest_port
		self.clientInfo['rtpAddr'] = dest_addr
		print("Sending to Addr:" + self.clientInfo['rtpAddr'] + ":" + str(self.clientInfo['rtpPort']))
		# Create a new socket for RTP/UDP
		self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.clientInfo['event'] = threading.Event()
		self.clientInfo['worker']= threading.Thread(target=self.sendRtp)
		self.clientInfo['worker'].start()


# Função para encerrar o servidor e as suas threads no momento do CTRL+C
def ctrlc_handler(sig, frame):
    print("A encerrar o servidor e as threads...")
    sys.exit(0)


def svc_answer_requests(port:int, db: Database):
	service_name = "svc_answer_requests"
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	endereco = "" # Listen on all interfaces
	server_socket.bind((endereco, port))
	print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

	while True:
		try:
			dados, addr = server_socket.recvfrom(1024)
			threading.Thread(target=handle_answer_requests, args=(dados, server_socket, addr, db)).start()
		except Exception as e:
			print(f"Erro svc_answer_requests: {e}")
			break

def handle_answer_requests(dados, socket, addr:tuple, db: Database):
	msg = Mensagem.deserialize(dados)
	print(f"Conversação estabelecida com {addr}")
	print(msg)
	if msg.get_tipo() == Mensagem.start_video:
		print("Chegou ao start_video")
		video = msg.get_dados()
		#! Envio de stream de video (talvez se faça um thread para isso)
		if not db.has_video(video):
			print(f"START_VIDEO without video: Não tenho o video {video}")
			raise Exception(f"START_VIDEO without video {video}")
		dest_addr = addr[0]
		dest_port = addr[1]
		(Servidor()).serve_movie(dest_addr, dest_port, video)
		response = f"A enviar o fluxo de video para {dest_addr} na porta {dest_port}"
		print(response)

	elif msg.get_tipo() == Mensagem.stop_video:
		###! UNFINISHED
		print("STOP_VIDEO-WIP")
		pass

	elif msg.get_tipo() == Mensagem.check_video:
		video = msg.get_dados()
		if db.has_video(video):
			print(f"Response check video: Tenho o video {video}")
			msg = Mensagem(Mensagem.resp_check_video, "my_ip", "1")
		else:
			print(f"Response check video: Não tenho o video {video}")
			msg = Mensagem(Mensagem.resp_check_video, "my_ip", "0")
		msg = msg.serialize()
		socket.sendto(msg, addr)

	elif msg.get_tipo() == Mensagem.metrica:
		###! UNFINISHED
		print("METRICA-WIP")
		pass

	else:
		print("Foi recebido uma mensagem desconhecida!!")
		

def main():

	db = Database()

	#! Talvez receba um ficheiro com a informação de configuração a dizer os movies que pode disponibilizar
	# if len(sys.argv) < 2:
	#     print(f"Uso: python3 {sys.argv[0]} <config_file.json>")
	#     sys.exit(1)
	# db.read_config_file(sys.argv[1])

	#! Introdução hardocded do video que tem
	db.add_video("movie.Mjpeg")



	# Regista o sinal para encerrar o servidor no momento do CTRL+C
	signal.signal(signal.SIGINT, ctrlc_handler)

	# Inicia os serviços em threads separadas
	svc1_thread = threading.Thread(target=svc_answer_requests, args=(3000, db))

	threads = [svc1_thread]

	for t in threads:
		t.daemon = True
	
	for t in threads:
		t.start()

	for t in threads:
		t.join()


if __name__ == '__main__':
	
	# dest_addr = "10.0.0.20"
	# dest_port = 25000
	# video = "movie.Mjpeg"
	# (Servidor()).main(dest_addr, dest_port, video)
	
	#####################

	main()


