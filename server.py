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
	def __init__(self, host, port, timeout, queueSize):
		"""
		creates tcp socket, binds to host and port, makes it listen
		"""
		self.host = host
		self.timeout = timeout
		self.socketVar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#SO_REUSEADDR allows reuse of sockets set in TIME_WAIT state
		#it also does not block all ports hence to be used if using HOST as ''
		self.socketVar.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		#timeout on accept function
		self.socketVar.setblocking(False)
		self.socketVar.bind((host, port))
		self.port = self.socketVar.getsockname()[1]
		self.socketVar.listen(queueSize)

	def accept(self):
		clientConnection, clientAddress = self.socketVar.accept()
		clientConnection.settimeout(self.timeout)
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
		self.documentRoot = config['DEFAULT']['DocumentRoot']
		if not os.path.exists(self.documentRoot):
			os.makedirs(self.documentRoot)
		self.logDir = config['DEFAULT']['LogDir']
		if not os.path.exists(self.logDir):
			os.makedirs(self.logDir)
		self.errLogPath = os.path.join(self.logDir, config['DEFAULT']['ErrorLog'])
		with open(self.errLogPath, "a"):
			pass
		self.accessLogPath = os.path.join(self.logDir, config['DEFAULT']['AccessLog'])
		with open(self.accessLogPath, "a"):
			pass
		self.postDataLogPath = os.path.join(self.logDir, config['DEFAULT']['PostDataLog'])
		with open(self.postDataLogPath, "a"):
			pass
		try:
			os.chmod(self.accessLogPath,0o666)
			os.chmod(self.errLogPath,0o666)
			os.chmod(self.postDataLogPath,0o666)
		except:
			pass
		self.activeConn = 0
		#A variable which contains all thread objects
		self.threads = []
		#variable to check if server is serving 1 - running, 0 - stopped
		self.status = 1
		self.loggerStatus = 1
		self.requestTimeout = float(config['DEFAULT']['RequestTimeout'])
		self.tcpSocket = tcpSocket(host, port, self.requestTimeout, int(config['DEFAULT']['QueueSize']))
		self.logQueue = queue.Queue(10)
		self.loggerThread = threading.Thread(target=self.logger)
		self.loggerThread.start()
		logging.basicConfig(filename=self.errLogPath, level=config['DEFAULT']['LogLevel'])
		sys.excepthook = self.error_logger

	def logger(self):
		try:
			if not os.path.exists(self.logDir):
				os.makedirs(self.logDir)
			f = open(self.accessLogPath, 'a')
			while(self.loggerStatus):
				try:
					log = self.logQueue.get(block=False)
				except queue.Empty:
					continue
				else:
					f.write(log+"\n")
			f.close()
		except:
			self.error_logger(sys.exc_info())

	def error_logger(self, *args):
		if(len(args) == 1):
			args = args[0]
		print(f"The server encountered a critical error and will stop now. A detailed log of this can be found in {self.errLogPath}")
		logging.critical(utils.logDate(), exc_info=(args[0], args[1], args[2]))
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
			'userAgent':'"-"',
			'cookie':'"-"',
			'set-cookie':'"-"'
		}
		try:
			while self.status:
				fullRequest = b''
				request = b''
				while(fullRequest.find('\r\n\r\n'.encode()) == -1):
					try:
						request = self.tcpSocket.receive(clientConnection, 1024)
						#to check if entire message sent at once
						fullRequest += request
					except socket.timeout:
						handler = requestHandlers.badRequest
						responseDict = handler('', '408',clientAddress)
						responseString = utils.responseBuilder(responseDict)
						self.tcpSocket.send(clientConnection, responseString)
						loggingInfo['time'] =  "["+utils.logDate()+"]"
						loggingInfo['statusCode'] = responseDict['statusLine']['statusCode']
						self.tcpSocket.close(clientConnection)
						self.activeConn-=1
						log = utils.logAccess(loggingInfo)
						self.logQueue.put(log)
						return
				loggingInfo['time'] =  "["+utils.logDate()+"]"
				parsedRequest = utils.requestParser(fullRequest)
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
				loggingInfo['set-cookie'] = '"'+f"{responseDict['responseHeaders'].get('Set-Cookie', '-')}"+'"'
				loggingInfo['requestLine'] = '"'+(fullRequest.split('\r\n'.encode(), 1)[0]).decode('utf-8')+'"'
				if('responseBody' in responseDict):
					loggingInfo['dataSize'] = len(responseDict['responseBody'])
				if(parsedRequest and 'user-agent' in parsedRequest["requestHeaders"]):
					loggingInfo['userAgent'] = f'"{parsedRequest["requestHeaders"]["user-agent"]}"'
				if(parsedRequest and 'referer' in parsedRequest["requestHeaders"]):
					loggingInfo['referer'] = f'"{parsedRequest["requestHeaders"]["referer"]}"'
				if(parsedRequest and 'cookie' in parsedRequest["requestHeaders"]):
					loggingInfo['cookie'] = f'"{parsedRequest["requestHeaders"]["cookie"]}"'
				log = utils.logAccess(loggingInfo)
				if(('Connection' in responseDict['responseHeaders']) and responseDict['responseHeaders']['Connection'].lower() == 'close'):
					self.tcpSocket.close(clientConnection)
					self.activeConn-=1
					self.logQueue.put(log)
					return
				else:
					self.logQueue.put(log)
		except:
			responseDict = requestHandlers.badRequest('', '500',clientAddress)
			responseString = utils.responseBuilder(responseDict)
			self.tcpSocket.send(clientConnection, responseString)
			self.tcpSocket.close(clientConnection)
			logging.error(utils.logDate(), exc_info=sys.exc_info())
	
	def serve(self):
		"""
		server serves requests
		"""
		try:
			print(f'Serving HTTP on port {self.tcpSocket.port} (stop/restart)...')
			while self.status:
				if(self.activeConn == self.maxConn):
					logging.info(f"{utils.logDate()}:Maximum simultaenous connections reached")
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
		except:
			self.error_logger(sys.exc_info())
	
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
		initialWait = self.requestTimeout
		for thread in self.threads:
			try:
				thread.join(initialWait)
				if(thread.is_alive()):
					initialWait=0
			except:
				pass
			finally:
				if(thread.is_alive()):
					logging.warning(f"{utils.logDate()}: A thread refused to join, may indicate a hanging thread or too small timeout")
		print("All pending requests served.")
		self.loggerStatus=0
		print("Waiting for logger to finish logging...")
		self.loggerThread.join()
		print("Server has stopped.")
		
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
			logging.info(f"{utils.logDate()}:Stopping server")
			server.stop()
			break
		elif(ip == 'restart'):
			logging.info(f"{utils.logDate()}:Restarting server")
			server.stop()
			#ensure previous server thread stopped
			serverThread.join()	
			print("Restarting Server")
			#start new server thread
			newServerThread = threading.Thread(target=server.serve)
			newServerThread.start()
		else:
			logging.info(f"{utils.logDate()}:Invalid option entered")
			print("Invalid Option")
	serverThread.join()	