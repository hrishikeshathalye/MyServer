import socket
import threading
import os
import sys
import queue
import utils
import configparser
import requestHandlers
import logging
#class to encapsulate most socket functions
class tcpSocket:
	def __init__(self, host, port):
		"""
		creates tcp socket, binds to host and port, makes it listen
		"""
		self.host = host
		self.socketVar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#SO_REUSEADDR allows reuse of sockets set in TIME_WAIT state
		#it also does not block all ports hence to be used if using HOST as ''
		self.socketVar.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		#timeout on accept function
		self.socketVar.setblocking(False)
		self.socketVar.bind((host, port))
		self.port = self.socketVar.getsockname()[1]
		self.socketVar.listen(100)

	def accept(self):
		clientConnection, clientAddress = self.socketVar.accept()
		clientConnection.settimeout(10.0)
		return clientConnection,clientAddress

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
		config = configparser.ConfigParser()
		config.read('conf/myserver.conf')
		self.maxConn = int(config['DEFAULT']['MaxSimultaneousConnections'])
		self.activeConn = 0
		#A variable which contains all thread objects
		self.threads = []
		#variable to check if server is serving 1 - running, 0 - stopped
		self.status = 1
		self.loggerStatus = 1
		self.tcpSocket = tcpSocket(host, port)
		self.logQueue = queue.Queue(10)
		self.loggerThread = threading.Thread(target=self.logger)
		self.loggerThread.start()
		logging.basicConfig(filename='log/error.log', level=config['DEFAULT']['LogLevel'])
		sys.excepthook = self.error_logger
		threading.excepthook = self.error_logger

	def logger(self):
		if not os.path.exists("log"):
			os.makedirs("log")
		f = open("log/access.log", 'a')
		while(self.loggerStatus):
			try:
				log = self.logQueue.get(block=False)
			except queue.Empty:
				continue
			else:
				f.write(log+"\n")
		f.close()

	def error_logger(self, *args):
		if(len(args) == 1):
			args = args[0]
		print("The server encountered an error and will stop now. A detailed log of this can be found in error.log")
		logging.exception(utils.logDate(), exc_info=(args[0], args[1], args[2]))
		self.stop()
		os._exit(1)

	def worker(self, clientConnection,clientAddress):
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
					self.activeConn-=1
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
						self.activeConn-=1
						return
					sizeRead+=len(tmpData)
					fullRequest += tmpData
				parsedRequest = utils.requestParser(fullRequest)
				#handle padding with blank space if content-length greater than body
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
				handler = switch.get(parsedRequest['requestLine']['method'], requestHandlers.badRequest)
			#only bad request handler inspects the second argument
			responseDict = handler(parsedRequest, '501',clientAddress)
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
				self.tcpSocket.close(clientConnection)
				self.activeConn-=1
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
			if(self.activeConn == self.maxConn):
				continue
			try:
				clientConnection,clientAddress = self.tcpSocket.accept()
				
				self.activeConn+=1
			except BlockingIOError:
				continue
			else:
				#had to declare daemon coupled with timeout in join due to a race condition in socket recv
				workerThread = threading.Thread(target=self.worker, args=(clientConnection,clientAddress), daemon=True)
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
		#timeout of 10s for the first hanging thread found
		#all others should have completed by then so 0 timeout for them
		initialWait = 10.0
		for thread in self.threads:
			thread.join(initialWait)
			if(thread.is_alive()):
				initialWait=0
		print("All pending requests served.")
		self.loggerStatus=0
		print("Waiting for logger to finish logging...")
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
	port = 0
	if(len(sys.argv)>1):
		port = int(sys.argv[1])
	server = Server('', port)
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