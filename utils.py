from datetime import datetime
import time
import math
import platform
from time import mktime
import random
import hashlib
import os
import json
import pathlib
def requestParser(requestStr):
		"""
		accept request string, return dictionary
		returning None indicates parsing error
		"""
		requestStr = requestStr.strip()
		#According to the RFC, the body starts after a \r\n\r\n sequence
		headerBodySplit = requestStr.split("\r\n\r\n".encode(), 1)
		reqlineAndHeaders = headerBodySplit[0].decode('utf-8')
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
		try:
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
		
		except IndexError:
			return None

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
        responseStr += headerKey+": "+headersDict[headerKey]+"\r\n"
    responseStr+="\r\n"
    responseStr = responseStr.encode()
    responseStr+=body
    return responseStr

def givePhrase(statusCode):
	lookup={
		"100" : "Continue",
		"101" : "Switching Protocols",
		"200" : "OK",
		"201" : "Created",
		"202" : "Accepted",
		"203" : "Non-Authoritative Information",
		"204" : "No Content",
		"205" : "Reset Content",
		"206" : "Partial Content",
		"300" : "Multiple Choices",
		"301" : "Moved Permanently",
		"302" : "Found",
		"303" : "See Other",
		"304" : "Not Modified",
		"305" : "Use Proxy",
		"307" : "Temporary Redirect",
		"400" : "Bad Request",
		"401" : "Unauthorized",
		"402" : "Payment Required",
		"403" : "Forbidden",
		"404" : "Not Found",
		"405" : "Method Not Allowed",
		"406" : "Not Acceptable",
		"407" : "Proxy Authentication Required",
		"408" : "Request Timeout",
		"409" : "Conflict",
		"410" : "Gone",
		"411" : "Length Required",
		"412" : "Precondition Failed",
		"413" : "Request Entity Too Large",
		"414" : "Request-URI Too Large",
		"415" : "Unsupported Media Type",
		"416" : "Requested range not satisfiable",
		"417" : "Expectation Failed",
		"500" : "Internal Server Error",
		"501" : "Not Implemented",
		"502" : "Bad Gateway",
		"503" : "Service Unavailable",
		"504" : "Gateway Time-out",
		"505" : "HTTP Version not supported"
	}
	return lookup[str(statusCode)]

def rfcDate(date):
	"""Return a string representation of a date according to RFC 1123
	(HTTP/1.1).
	"""
	dt = date
	weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
	month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month - 1]
	return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month, dt.year, dt.hour, dt.minute, dt.second)

def logDate():
	timezone = -time.timezone/3600
	timezoneH = math.floor(timezone)
	timezoneM = int((timezone-timezoneH)*60)
	dt = datetime.now()
	month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month - 1]
	date = "%02d/%s/%04d:%02d:%02d:%02d +" % (dt.day, month, dt.year, dt.hour, dt.minute, dt.second)
	date+=str(timezoneH)
	date+=str(timezoneM)
	return date

def logAccess(loggingInfo):
	log = ""
	for i in loggingInfo:
		log+=str(loggingInfo[i])+" "
	return log

def prioritizeEncoding(acceptVal):
	"""
	takes in accept-encoding header value(str) and returns 
	which encoding to use according to q priority
	"""
	if(acceptVal == ""):
		return "identity"
	allEncodings = [
		"br",
		"compress",
		"deflate",
		"gzip",
		"exi",
		"pack200-gzip",
		"x-compress",
		"x-gzip",
		"zstd"
	]
	priority=dict()
	tmp = acceptVal.split(',')
	starPriority = 0
	seenEncodings = []
	pflag = 0
	for i in tmp:
		i = i.strip()
		pair = i.split(';')
		encoding = pair[0].strip()
		seenEncodings.append(encoding)
		if len(pair) == 1:
			pair.append("q=1.0")
		q = float(pair[1].split("=")[1].strip())
		if(q == 0.0):
			if(encoding=="identity"):
				pflag = 1
			continue
		if(encoding!="*"):
			priority[encoding] = q
		else:
			starPriority = q
	if(starPriority):
		for i in allEncodings:
			if(i not in seenEncodings):
				priority[i] = starPriority
	try:
		priority['identity'] = 1
		if pflag == 1:
			priority.pop(encoding, None)
		return max(priority, key=priority.get)

	except ValueError:
		return None

def prioritizeMedia(acceptVal,extension,path):
	"""
	takes in accept-media header value(str) and returns 
	which media type to use according to q priority
	"""
	if(acceptVal == ""):
		return "application/example"
	with open('media-types/content-qvals.json','r') as jf:
		priority = json.load(jf)
	tmp = acceptVal.split(',')
	for i in tmp:
		i = i.strip()
		pair = i.split(';')
		broadtype = pair[0].strip()
		mtype = broadtype.split("/")[0]
		subtype = broadtype.split("/")[1]
		if len(pair) == 1:
			pair.append("q=1.0")
		try:
			q = float(pair[1].split("=")[1].strip())
		except ValueError:
			q = float(pair[2].split("=")[1].strip())
		tag = pair[1].split("=")[0].strip()
		if broadtype == "*/*" :
			q -= 0.000001
		if tag == "level":
			q += 0.01
		if(subtype != "*"):
			if mtype + "/" + subtype not in priority.keys():
				q = 0
				
			priority[mtype + "/" + subtype] = q
		else:
			for key in priority.keys():
				if key.split("/")[0] == mtype:
					if key not in priority.keys():
						q = 0.00000001
					priority[key] = q - 0.00000001
	sortedpriority = sorted(priority.items(), key=lambda x: x[1],reverse = True)
	for key in sortedpriority:
		if key[1] != 0 and (os.path.isfile(path.rstrip(pathlib.Path(path).suffix) + "." + key[0].split("/")[1]) or key[0].split("/")[1] == "*"):
			return key[0].split("/")[1]
	return -1

def getServerInfo():
	serverName = "MyServer"
	serverVersion = "1.0"
	opSys = platform.platform()
	info = f'{serverName}/{serverVersion} ({opSys})'
	return info

def compatCheck(httpVersion):
	protocol = httpVersion.split('/')[0].strip()
	version = httpVersion.split('/')[1].strip()
	return (math.floor(float(version)) == 1 ) and (protocol=='HTTP')

def compareDate(ifmod, lastmod,currdate,statuscode,flag):
	ifmod_sec = mktime(time.strptime(ifmod,'%a, %d %b %Y %H:%M:%S %Z'))
	lastmod_sec = mktime(time.strptime(lastmod,'%a, %d %b %Y %H:%M:%S %Z'))
	currdate_sec = mktime(time.strptime(currdate,'%a, %d %b %Y %H:%M:%S %Z'))
	if ifmod_sec < lastmod_sec or ifmod_sec > currdate_sec:
		if flag:
			return statuscode
		else:
			return '200'
	else:
		return '304'

def compareDate2(ifunmod, lastmod,statuscode):
	ifunmod_sec = mktime(time.strptime(ifunmod,'%a, %d %b %Y %H:%M:%S %Z'))
	lastmod_sec = mktime(time.strptime(lastmod,'%a, %d %b %Y %H:%M:%S %Z'))
	if ifunmod_sec > lastmod_sec:
		return statuscode
	else:
		return '412'

def makecookie(path,ip,date):
	allowedChar = '123456789abcdef'
	value = path + ip[0] + date 
	for i in range(5):
		value += random.choice(allowedChar)
	value = hashlib.md5(value.encode()).hexdigest()
	invalid = ['22','2c','3b','5c']
	for i in invalid:
		for j in range(0,len(value),2):
			if i == value[j:j+2]:
				vlist = list(value)
				vlist[j:j+2] = [random.choice(allowedChar), random.choice(allowedChar)]
				j -= 2
				value = ''.join(vlist)
	cook = dict()
	cook['mycookie'] = value
	return cook

	
def ifmatchparser(ifmatch):
	return ifmatch.split(',')

def parsecookie(cookie):
	cookielist = cookie.split(';')
	cook = dict()
	for c in cookielist:
		cook[c.split('=')[0]] = c.split('=')[1]
	return cook	


