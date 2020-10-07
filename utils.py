def requestParser(requestStr):
		"""
		accept request string, return dictionary
		"""
		requestStr = requestStr.strip()
		#According to the RFC, the body starts after a \r\n\r\n sequence
		headerBodySplit = requestStr.split("\r\n\r\n", 1)
		reqlineAndHeaders = headerBodySplit[0]
		requestBody = ''
		#since the body maybe absent sometimes, this avoids an IndexError
		if(len(headerBodySplit)>1):
			requestBody = headerBodySplit[1]
		
		headerFields = reqlineAndHeaders.strip().split('\r\n')
		#RFC : Request-Line = Method SP Request-URI SP HTTP-Version CRLF
		requestFields = headerFields[0].split(" ")
		requestHeaders = headerFields[1:]
		requestLine = dict()
		requestLine['method'] = requestFields[0]
		#Request-URI = "*" | absoluteURI | abs_path | authority
		requestLine['requestUri'] = requestFields[1]
		requestLine['httpVersion'] = requestFields[2]

		headersDict = dict()
		for i in requestHeaders:
			keyValSplit = i.split(':', 1)
			key = keyValSplit[0]
			val = keyValSplit[1]
			#lower used since according to RFC, header keys are case insensitive
			#Some values maybe case sensitive or otherwise, depending on key, THAT CASE NOT HANDLED
			headersDict[key.strip().lower()] = val.strip()
		
		requestHeaders = headersDict
		"""
		    request-header = Accept	   ; Section 14.1
        	| Accept-Charset		   ; Section 14.2
        	| Accept-Encoding          ; Section 14.3
        	| Accept-Language          ; Section 14.4
            | Authorization            ; Section 14.8
            | Expect                   ; Section 14.20
            | From                     ; Section 14.22
            | Host                     ; Section 14.23
            | If-Match                 ; Section 14.24
			| If-Modified-Since        ; Section 14.25
            | If-None-Match            ; Section 14.26
            | If-Range                 ; Section 14.27
            | If-Unmodified-Since      ; Section 14.28
            | Max-Forwards             ; Section 14.31
            | Proxy-Authorization      ; Section 14.34
            | Range                    ; Section 14.35
            | Referer                  ; Section 14.36
            | TE                       ; Section 14.39
            | User-Agent               ; Section 14.43
		"""
		#At this point requestLine(dictionary), headers(dictionary) and body(string) constitute the entire message
		#uncomment line below if debugging to compare with original requestStr
		#print(requestStr)
		parsedRequest = {
			'requestLine': requestLine, 
			'requestHeaders': requestHeaders, 
			'requestBody': requestBody
		}
		return parsedRequest

def responseBuilder(statusLine, headersDict, body):
	"""
	accept dictionary, build response string
	"""
	pass
