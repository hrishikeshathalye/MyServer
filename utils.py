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
		#At this point requestLine(dictionary), requestHeaders(dictionary) and requestBody(string) constitute the entire message
		#uncomment line below if debugging to compare with original requestStr
		#print(requestStr)
		parsedRequest = {
			'requestLine': requestLine, 
			'requestHeaders': requestHeaders, 
			'requestBody': requestBody
		}
		return parsedRequest

def responseBuilder(responseDict):
    """
	accept dictionary, build response string
    """
    #Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
    statusLine = responseDict['statusLine']['httpVersion'] + " "
    statusLine += responseDict['statusLine']['statusCode'] + " "
    statusLine += responseDict['statusLine']['reasonPhrase']
    headersDict = responseDict['responseHeaders']
    body = responseDict['responseBody']
    responseStr = statusLine + "\r\n"
    for headerKey in headersDict:
        responseStr = headerKey+": "+headersDict[headerKey]+"\r\n"
    responseStr+="\r\n"
    responseStr+=body
    return responseStr
