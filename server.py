import socket
import threading

#class to encapsulate most socket functions
class tcpSocket:
	def __init__(self, host, port):
		"""
		creates tcp socket, binds to host and port, makes it listen
		"""
		self.socketVar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#SO_REUSEADDR allows reuse of sockets set in TIME_WAIT state
		#it also does not block all ports hence to be used if using HOST as ''
		self.socketVar.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socketVar.bind((host, port))
		self.socketVar.listen(5)
		print(f'Serving HTTP on port {port} ...')

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
		self.tcpSocket = tcpSocket(host, port)
		self.utils = utils()

	def worker(self):
		"""
		server spawns worker threads
		"""
		request = self.tcpSocket.receive('utf-8')
		self.utils.requestParser(request)
		response = "HTTP/1.1 200 OK\r\n\r\nHello, World!"
		self.tcpSocket.send(response, 'utf-8')
		self.tcpSocket.close()

	def serve(self):
		"""
		server serves requests
		"""
		while True:
			self.tcpSocket.accept()
			handlerThread = threading.Thread(target=self.worker)
			#declaring threads as daemons so that the threads do not block program exit and terminate on program exit
			handlerThread.daemon = True
			handlerThread.start()
		
if __name__ == "__main__":
	#An instance of a multithreaded server
	server = Server('', 90)
	server.serve()