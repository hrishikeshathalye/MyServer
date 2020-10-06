import socket
import threading
import sys
import os

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

class utils():
	#class to encapsulate helper utils
	def requestParser(self, requestStr):
		"""
		accept request string, return dictionary
		"""
		requestStr = requestStr.strip()
		#According to the RFC, the body starts after a \r\n\r\n sequence
		headerBodySplit = requestStr.split("\r\n\r\n", 1)
		reqlineAndHeaders = headerBodySplit[0]
		body = ''
		#since the body maybe absent sometimes, this avoids an IndexError
		if(len(headerBodySplit)>1):
			body = headerBodySplit[1]
		
		headerFields = reqlineAndHeaders.strip().split('\r\n')
		requestLine = headerFields[0]
		headers = headerFields[1:]

		headersDict = dict()
		for i in headers:
			keyValSplit = i.split(':', 1)
			key = keyValSplit[0]
			val = keyValSplit[1]
			#lower used since according to RFC, header keys are case insensitive
			#Some values maybe case sensitive or otherwise, depending on key, THAT CASE NOT HANDLED
			headersDict[key.strip().lower()] = val.strip()
		
		headers = headersDict
		#At this point requestLine(string), headers(dictionary) and body(string) constitute the entire message
		#uncomment line below if debugging to compare with original requestStr
		#print(requestStr)
		print("Request Line :")
		print(requestLine)
		print("Headers :")
		print(headers)
		print("Body :")
		print(body)

	def responseBuilder(self, statusLine, headersDict, body):
		"""
		accept dictionary, build response string
		"""
		pass

class Server:	
	def __init__(self, host, port):
		#A variable which contains all thread objects
		self.threads = []
		#variable to check if server is serving 1 - running, 0 - stopped
		self.status = 0
		self.tcpSocket = tcpSocket(host, port)
		#timeout on accept function
		self.tcpSocket.socketVar.settimeout(0)
		self.utils = utils()

	def worker(self):
		"""
		server spawns worker threads
		"""
		self.tcpSocket.clientConnection.settimeout(5.0)
		try:
			request = self.tcpSocket.receive('utf-8')
			self.utils.requestParser(request)
			response = "HTTP/1.1 200 OK\r\n\r\nHello, World!"
			self.tcpSocket.send(response, 'utf-8')
		except:
			pass
		finally:
			self.tcpSocket.close()
		
	def serve(self):
		"""
		server serves requests
		"""
		print(f'Serving HTTP on port {self.tcpSocket.port}...')
		self.status = 1
		while self.status:
			try:
				self.tcpSocket.accept()
			except:
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