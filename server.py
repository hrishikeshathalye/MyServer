import socket
import threading
import utils
import requestHandlers
#class to encapsulate most socket functions
class tcpSocket:
	def __init__(self, host, port):
		"""
		creates tcp socket, binds to host and port, makes it listen
		"""
		self.host = host
		self.port = port
		self.socketVar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#SO_REUSEADDR allows reuse of sockets set in TIME_WAIT state
		#it also does not block all ports hence to be used if using HOST as ''
		self.socketVar.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socketVar.bind((host, port))
		self.socketVar.listen(5)

	def accept(self):
		self.clientConnection, self.clientAddress = self.socketVar.accept()

	def receive(self, decodingScheme):
		"""
		receive and decode according to passed scheme
		"""
		return self.clientConnection.recv(1024).decode(decodingScheme)

	def send(self, response, encodingScheme):
		"""
		encodes and sends
		"""
		self.clientConnection.sendall(response.encode(encodingScheme))
	
	def close(self):
		self.clientConnection.close()
	
class Server:	
	def __init__(self, host, port):
		#A variable which contains all thread objects
		self.threads = []
		#variable to check if server is serving 1 - running, 0 - stopped
		self.status = 0
		self.tcpSocket = tcpSocket(host, port)
		#timeout on accept function
		self.tcpSocket.socketVar.settimeout(0)

	def worker(self):
		"""
		server spawns worker threads
		"""
		self.tcpSocket.clientConnection.settimeout(10.0)
		fullRequest = ''
		request = ''
		while(fullRequest.find('\r\n\r\n') == -1):
			try:
				request = self.tcpSocket.receive('utf-8')
				#to check if entire message sent at once
				fullRequest += request
			except socket.timeout:
				self.tcpSocket.close()
				return
		parsedRequest = utils.requestParser(fullRequest)
		if(('content-length' in parsedRequest['requestHeaders']) or ('transfer-encoding' in parsedRequest['requestHeaders'])):
			contentLength = int(parsedRequest['requestHeaders']['content-length'])
			sizeRead=0 #bytes read till now
			#you indicated a non zero content length but did not give further data so wait to get data
			while(sizeRead<contentLength):
				#data parsed till now is already >= content-length so break
				if(len(parsedRequest['requestBody'])>=contentLength):
					break
				try:
					tmpData = self.tcpSocket.clientConnection.recv(contentLength-sizeRead)
				except socket.timeout:
					self.tcpSocket.close()
					return
				sizeRead+=len(tmpData)
				fullRequest += tmpData.decode('utf-8')
			parsedRequest = utils.requestParser(fullRequest)
			#handle padding with blank space if content-length greater than body
			#handle shortening of body in case of entire body at once (handled)
			parsedRequest['requestBody'] = parsedRequest['requestBody'][0:contentLength]
		switch={
			'GET': requestHandlers.get,
			'POST': requestHandlers.post,
			'PUT': requestHandlers.put,
			'HEAD': requestHandlers.head,
			'DELETE': requestHandlers.delete,
		}
		handler = switch.get(parsedRequest['requestLine']['method'], requestHandlers.other)
		responseDict = handler(parsedRequest)
		responseString = utils.responseBuilder(responseDict)
		self.tcpSocket.send(responseString, 'utf-8')
		self.tcpSocket.close()
		
	def serve(self):
		"""
		server serves requests
		"""
		print(f'Serving HTTP on port {self.tcpSocket.port} (stop/restart)...')
		self.status = 1
		while self.status:
			try:
				self.tcpSocket.accept()
			except BlockingIOError:
				continue
			else:
				workerThread = threading.Thread(target=self.worker)
				self.threads.append(workerThread)
				workerThread.start()
	
	def stop(self):
		"""
		joins all threads
		stops server, then returns 1
		"""
		#dont accept any new requests
		self.status = 0
		print("Waiting for all pending requests to complete...")
		#serve pending requests
		for thread in self.threads:
			thread.join()
		print("All pending requests served.")
		print("Server has stopped.")

	# def restart(self):
	# 	"""
	# 	restarts the server
	# 	"""
	# 	self.stop()
	# 	print("Restarting Server")
	# 	self.serve()
		
if __name__ == "__main__":
	#An instance of a multithreaded server
	server = Server('', 90)
	#The action of serving is a seperate thread since main needs to also accept input
	#and the normal behavior of serve is blocking in nature
	serverThread = threading.Thread(target=server.serve)
	serverThread.start()
	while True:
		ip = input()
		ip = ip.lower()
		if(ip == 'stop'):
			server.stop()
			break
		elif(ip == 'restart'):
			server.stop()
			#ensure previous server thread stopped
			serverThread.join()	
			print("Restarting Server")
			#start new server thread
			serverThread = threading.Thread(target=server.serve)
			serverThread.start()
		else:
			print("Invalid Option")
	serverThread.join()	