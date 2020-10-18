import socket
import threading
import os
import queue
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
		#timeout on accept function
		self.socketVar.settimeout(0)
		self.socketVar.bind((host, port))
		self.socketVar.listen(5)

	def accept(self):
		clientConnection, clientAddress = self.socketVar.accept()
		clientConnection.settimeout(10.0)
		return clientConnection

	def receive(self, clientConnection, bufSize):
		"""
		receive and decode according to passed scheme
		"""
		return clientConnection.recv(bufSize)

	def send(self, clientConnection, response):
		"""
		encodes and sends
		"""
		clientConnection.sendall(response)
	
	def close(self, clientConnection):
		clientConnection.close()
	
class Server:	
	def __init__(self, host, port):
		#A variable which contains all thread objects
		self.threads = []
		#variable to check if server is serving 1 - running, 0 - stopped
		self.status = 1
		self.loggerStatus = 1
		self.tcpSocket = tcpSocket(host, port)
		self.logQueue = queue.Queue(10)
		self.loggerThread = threading.Thread(target=self.logger)
		self.loggerThread.start()

	def logger(self):
		f = open("log/access.log", 'a')
		while(True):
			try:
				log = self.logQueue.get(block=False)
			except queue.Empty:
				if(self.loggerStatus):
					continue
				else:
					break
			else:
				f.write(log+"\n")
				f.flush()
				os.fsync(f.fileno())
		f.close()

	def worker(self, clientConnection):
		"""
		server spawns worker threads
		"""
		loggingInfo={
			'laddr':clientConnection.getpeername()[0],
			'identity':'-',
			'userid':'-',
			'time':'-',
			'requestLine':'"-"',
			'statusCode':'-',
			'dataSize':0,
			'referer':'"-"',
			'userAgent':'"-"'
		}
		while self.status:
			fullRequest = b''
			request = b''
			while(fullRequest.find('\r\n\r\n'.encode()) == -1):
				try:
					request = self.tcpSocket.receive(clientConnection, 1024)
					#to check if entire message sent at once
					fullRequest += request
				except socket.timeout:
					self.tcpSocket.close(clientConnection)
					return
			loggingInfo['time'] =  "["+utils.logDate()+"]"
			parsedRequest = utils.requestParser(fullRequest)
			#('transfer-encoding' in parsedRequest['requestHeaders']) was below
			if(parsedRequest and ('content-length' in parsedRequest['requestHeaders'])):
				contentLength = int(parsedRequest['requestHeaders']['content-length'])
				sizeRead=0 #bytes read till now
				#you indicated a non zero content length but did not give further data so wait to get data
				while(sizeRead<contentLength):
					#data parsed till now is already >= content-length so break
					if(len(parsedRequest['requestBody'])>=contentLength):
						break
					try:
						tmpData = self.tcpSocket.receive(clientConnection, contentLength-sizeRead)
					except socket.timeout:
						self.tcpSocket.close(clientConnection)
						return
					sizeRead+=len(tmpData)
					fullRequest += tmpData
				parsedRequest = utils.requestParser(fullRequest)
				#handle padding with blank space if content-length greater than body
				#handle shortening of body in case of entire body at once (handled)
				parsedRequest['requestBody'] = parsedRequest['requestBody'][0:contentLength]
			elif(parsedRequest):
				parsedRequest['requestBody'] = ''.encode()

			switch={
				'GET': requestHandlers.get,
				'POST': requestHandlers.post,
				'PUT': requestHandlers.put,
				'HEAD': requestHandlers.head,
				'DELETE': requestHandlers.delete,
			}
			if(parsedRequest == None):
				handler = requestHandlers.badRequest
			else:
				handler = switch.get(parsedRequest['requestLine']['method'], requestHandlers.other)
			responseDict = handler(parsedRequest)
			responseString = utils.responseBuilder(responseDict)
			self.tcpSocket.send(clientConnection, responseString)
			loggingInfo['statusCode'] = responseDict['statusLine']['statusCode']
			loggingInfo['requestLine'] = '"'+(fullRequest.split('\r\n'.encode(), 1)[0]).decode('utf-8')+'"'
			if('responseBody' in responseDict):
				loggingInfo['dataSize'] = len(responseDict['responseBody'])
			if(parsedRequest and 'user-agent' in parsedRequest["requestHeaders"]):
				loggingInfo['userAgent'] = f'"{parsedRequest["requestHeaders"]["user-agent"]}"'
			if(parsedRequest and 'referer' in parsedRequest["requestHeaders"]):
				loggingInfo['referer'] = f'"{parsedRequest["requestHeaders"]["referer"]}"'
			log = utils.logAccess(loggingInfo)
			if(('Connection' in responseDict['responseHeaders']) and responseDict['responseHeaders']['Connection'].lower() == 'close'):
				# clientConnection.shutdown(socket.SHUT_RDWR)
				self.tcpSocket.close(clientConnection)
				self.logQueue.put(log)
				return
			else:
				self.logQueue.put(log)
	
	def serve(self):
		"""
		server serves requests
		"""
		print(f'Serving HTTP on port {self.tcpSocket.port} (stop/restart)...')
		while self.status:
			try:
				clientConnection = self.tcpSocket.accept()
			except BlockingIOError:
				continue
			else:
				workerThread = threading.Thread(target=self.worker, args=(clientConnection,))
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
		self.loggerStatus=0
		self.loggerThread.join()
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