import socket
import threading
import os
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

	def receive(self, clientConnection, bufSize , decodingScheme):
		"""
		receive and decode according to passed scheme
		"""
		return clientConnection.recv(bufSize).decode(decodingScheme)

	def send(self, clientConnection, response, encodingScheme):
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
		self.logQueue = []
		self.logLock = threading.Lock()
		self.loggerThread = threading.Thread(target=self.logger)
		self.loggerThread.start()

	def logger(self):
		f = open("log/access.log", 'a')
		while(self.loggerStatus):
			while(len(self.logQueue)):
				with self.logLock:
					f.write(self.logQueue.pop(0)+"\n")
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
			fullRequest = ''
			request = ''
			while(fullRequest.find('\r\n\r\n') == -1):
				try:
					request = self.tcpSocket.receive(clientConnection, 1024 ,'utf-8')
					#to check if entire message sent at once
					fullRequest += request
				except socket.timeout:
					self.tcpSocket.close(clientConnection)
					return
			loggingInfo['time'] =  "["+utils.logDate()+"]"
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
						tmpData = self.tcpSocket.receive(clientConnection, contentLength-sizeRead, 'utf-8')
					except socket.timeout:
						self.tcpSocket.close(clientConnection)
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
			self.tcpSocket.send(clientConnection, responseString, 'utf-8')
			loggingInfo['statusCode'] = responseDict['statusLine']['statusCode']
			loggingInfo['requestLine'] = '"'+fullRequest.split('\r\n', 1)[0]+'"'
			if('responseBody' in responseDict):
				loggingInfo['dataSize'] = len(responseDict['responseBody'])
			if('user-agent' in parsedRequest["requestHeaders"]):
				loggingInfo['userAgent'] = f'"{parsedRequest["requestHeaders"]["user-agent"]}"'
			if('referer' in parsedRequest["requestHeaders"]):
				loggingInfo['referer'] = f'"{parsedRequest["requestHeaders"]["referer"]}"'
			log = utils.logAccess(loggingInfo)
			if(('Connection' in responseDict['responseHeaders']) and responseDict['responseHeaders']['Connection'].lower() == 'close'):
				# clientConnection.shutdown(socket.SHUT_RDWR)
				self.tcpSocket.close(clientConnection)
				with self.logLock:
					self.logQueue.append(log)
				return
			else:
				with self.logLock:
					self.logQueue.append(log)
	
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