from random import randint
import sys, traceback, threading, socket

from aux.VideoStream import VideoStream
from aux.RtpPacket import RtpPacket

from Databases.database_server import Database_Server
from aux.mensagem import Mensagem
from aux.utils import change_terminal_title
import signal

V_CHECK_PORT = 3001 #> Porta de atendimento do serviço check_videos
V_START_PORT = 3002 #> Porta de atendimento do serviço start_videos
V_STOP_PORT = 3003 #> Porta de atendimento do serviço stop_videos
METRICS_PORT = 3010 #> Porta de atendimento do serviço measure_metrics

class ServerWorker:	

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
					packet =  ServerWorker.makeRtp(data, frameNumber)
					self.clientInfo['rtpSocket'].sendto(packet,(address,port))
				except:
					print("Connection Error")
					print('-'*60)
					traceback.print_exc(file=sys.stdout)
					print('-'*60)
		# Close the RTP socket
		self.clientInfo['rtpSocket'].close()
		# print("All done!")

	@staticmethod
	def makeRtp(payload, frameNbr):
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
		# print("Encoding RTP Packet: " + str(seqnum))
		
		return rtpPacket.getPacket()

	def stop_serving(self):
		self.clientInfo['event'].set()

	def serve_movie(self, dest_addr:str, dest_port:int, movie_name:str, videos_dir:str="./videos/"):
		# Para indicar onde os filmes estão guardados
		filename = f"{videos_dir}{movie_name}" # talvez acrescentar no formated string "{movie_name}.Mjpeg"

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

#################################################################################################################
#* Serviço de CHECK_VIDEO que responde com os videos que tem
def svc_check_video(port:int, db: Database_Server):
	service_name = "svc_check_video"
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	endereco = "" # Listen on all interfaces
	server_socket.bind((endereco, port))
	print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

	while True:
		try:
			dados, addr = server_socket.recvfrom(1024)
			threading.Thread(target=handle_check_video, args=(dados, server_socket, addr, db)).start()
		except Exception as e:
			print(f"Erro svc_answer_requests: {e}")
			break

def handle_check_video(dados, socket, addr:tuple, db: Database_Server):
	msg = Mensagem.deserialize(dados)
	print(f"CHECK_VIDEO: Received from {addr}")
	# print(msg)

	if msg.get_tipo() == Mensagem.CHECK_VIDEO:
		videos = db.get_videos()
		msg = Mensagem(Mensagem.RESP_CHECK_VIDEO, dados=videos).serialize()
		socket.sendto(msg, addr)
		print(f"CHECK_VIDEO: respondido com os videos {videos} para {addr}")

	else:
		print("Foi recebido uma mensagem no serviço de CHEKC_VIDEO que não é de CHEKC_VIDEO type!!")

#################################################################################################################
#* Serviço de START_VIDEO que inicia o envio de um video
def svc_start_video(port:int, db: Database_Server):
	service_name = "svc_start_video"
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	endereco = "" # Listen on all interfaces
	server_socket.bind((endereco, port))
	print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

	while True:
		try:
			dados, addr = server_socket.recvfrom(1024)
			threading.Thread(target=handle_start_video, args=(dados, server_socket, addr, db)).start()
		except Exception as e:
			print(f"Erro svc_start_video: {e}")
			break

def handle_start_video(dados, socket, addr:tuple, db: Database_Server):
	msg = Mensagem.deserialize(dados)
	print(f"START_VIDEO: Received from {addr}")
	
	if msg.get_tipo() == Mensagem.START_VIDEO:
		video = msg.get_dados()
		if not db.has_video(video):
			print(f"START_VIDEO: Não tenho o video '{video}'!!!")
			raise Exception(f"START_VIDEO without video '{video}'!!!")
		
		if not db.is_streaming(video): # só inicia a stream do vídeo se não estiver a emiti-lo
			dest_addr = addr[0]
			dest_port = addr[1]
			sw = ServerWorker()
			sw.serve_movie(dest_addr, dest_port, video, videos_dir=db.get_videos_dir())
			db.add_stream(video,sw)
			print(f"START_VIDEO: A enviar o fluxo do video '{video}' para {dest_addr}:{dest_port}")
		else:
			# Caso em que recebeu um pedido de start_video de um vídeo mas que já está a ser emitido (Impossível de acontecer, só para debug)
			raise Exception(f"Já iniciei o vídeo '{video}'")
	else:
		print("Foi recebido uma mensagem no serviço de START_VIDEO que não é de START_VIDEO type!!")

#################################################################################################################
#* Serviço de STOP_VIDEO que para o envio de um video
def svc_stop_video(port:int, db: Database_Server):
	service_name = "svc_stop_video"
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	endereco = "" # Listen on all interfaces
	server_socket.bind((endereco, port))
	print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

	while True:
		try:
			dados, addr = server_socket.recvfrom(1024)
			threading.Thread(target=handle_stop_video, args=(dados, server_socket, addr, db)).start()
		except Exception as e:
			print(f"Erro svc_stop_video: {e}")
			break

def handle_stop_video(dados, socket, addr:tuple, db: Database_Server):
	msg = Mensagem.deserialize(dados)

	if msg.get_tipo() == Mensagem.STOP_VIDEO:
		video = msg.get_dados()
		print(f"STOP_VIDEO: {addr} pediu para parar a transmissão do vídeo {video}")
		db.remove_stream(video) # termina o worker que trata de enviar o vídeo e remove-o da base de dados

	else:
		print("Foi recebido uma mensagem no serviço de STOP_VIDEO que não é de STOP_VIDEO type!!")

#################################################################################################################
#* Serviço de MÉTRICA que responde com aos pacotes do RP com um TIMESTAMP
def svc_answer_metrics(port:int, db: Database_Server):
	service_name = "svc_answer_metrics"
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	endereco = "" # Listen on all interfaces
	server_socket.bind((endereco, port))
	print(f"Serviço '{service_name}' pronto para receber conexões na porta {port}")

	while True:
		try:
			dados, addr = server_socket.recvfrom(1024)
			threading.Thread(target=handle_answer_metrics, args=(dados, server_socket, addr, db)).start()
		except Exception as e:
			print(f"Erro svc_answer_metrics: {e}")
			break

def handle_answer_metrics(dados, socket, addr:tuple, db: Database_Server):
	msg = Mensagem.deserialize(dados)

	if msg.get_tipo() == Mensagem.METRICA:
		msg.update_timestamp()
		socket.sendto(msg.serialize(), addr)
		#? print(f"Métrica de {addr}, respondida.") # Print demasiado poluente
	else:
		print("Foi recebido uma mensagem no serviço de Métrica, cuja mensagem não é do tipo MÉTRICA!!")


#################################################################################################################

def main():
	change_terminal_title()
	# Regista o sinal para encerrar o servidor no momento do CTRL+C
	signal.signal(signal.SIGINT, ctrlc_handler)

	db = Database_Server()

	db.read_config_file(sys.argv[1])

	# Inicia os serviços em threads separadas
	svc1_thread = threading.Thread(target=svc_check_video, args=(V_CHECK_PORT, db))
	svc2_thread = threading.Thread(target=svc_start_video, args=(V_START_PORT, db))
	svc3_thread = threading.Thread(target=svc_stop_video, args=(V_STOP_PORT, db))
	svc4_thread = threading.Thread(target=svc_answer_metrics, args=(METRICS_PORT, db))

	threads = [
		svc1_thread, 
		svc2_thread,
		svc3_thread,
		svc4_thread,
	]

	for t in threads:
		t.daemon = True
	
	for t in threads:
		t.start()

	for t in threads:
		t.join()


if __name__ == '__main__':
	
	main()
