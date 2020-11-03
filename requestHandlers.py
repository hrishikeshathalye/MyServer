#module to handle all kinds of requests
import utils
from urllib.parse import urlparse, parse_qs
import configparser
import os, hashlib
import codecs
import pathlib
import json
import gzip
import zlib
import brotli
import lzw3
from datetime import datetime
from time import mktime
import time
import shutil
#pass parsed request to these functions
#expect them to return the response fields as a dictionary
#call utils.responseBuilder in main

"""
general-header = 
    Cache-Control            ; Section 14.9
    (Done) Connection               ; Section 14.10
    (Done) Date                     ; Section 14.18
    Pragma                   ; Section 14.32
    Trailer                  ; Section 14.40
    (Not to be Done) Transfer-Encoding        ; Section 14.41
    Upgrade                  ; Section 14.42
    Via                      ; Section 14.45
    *Warning                  ; Section 14.46
"""

#following requestHeaders to be handled
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
"""
    response-header = 
    Accept-Ranges           ; Section 14.5
    Age                     ; Section 14.6
    ETag                    ; Section 14.19
    Location                ; Section 14.30
    Proxy-Authenticate      ; Section 14.33
    Retry-After             ; Section 14.37
    Server                  ; Section 14.38
    Vary                    ; Section 14.44
    WWW-Authenticate        ; Section 14.47
"""
"""
    entity-header  = 
    Allow                    ; Section 14.7
    (Done)Content-Encoding         ; Section 14.11
    Content-Language         ; Section 14.12
    Content-Length           ; Section 14.13
    Content-Location         ; Section 14.14
    (Done for POST, PUT)Content-MD5              ; Section 14.15
    Content-Range            ; Section 14.16
    Content-Type             ; Section 14.17
    Expires                  ; Section 14.21
    Last-Modified            ; Section 14.29
    extension-header
"""
#Following are the supported media types		
"""
    application
    example
    image
    text
    audio
    video
    font 
    model
"""


def get(requestDict, *args):
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    requestLine = requestDict['requestLine']
    requestHeaders = requestDict['requestHeaders']
    acceptencoding = requestHeaders.get('accept-encoding',"")
    contentencoding = utils.prioritizeEncoding(acceptencoding)
    if not contentencoding:
        return badRequest(requestDict, '406')
    uri = requestLine['requestUri'] 
    uri = uri.lstrip('/')
    path = urlparse(uri).path
    with open('media-types/content-type.json','r') as jf:
        typedict = json.load(jf) 
    path = path.lstrip('/')    
    path = '/' + path
    if path == '/':
        path = '/index.html'  
    path = config['DEFAULT']['DocumentRoot'] + path
    
    if not os.path.isfile(path):
        return badRequest(requestDict, '404')

    dm = datetime.fromtimestamp(mktime(time.gmtime(os.path.getmtime(path))))
    ifmod = requestHeaders.get('if-modified-since',utils.rfcDate(datetime.fromtimestamp(0)))         
    ifunmod = requestHeaders.get('if-unmodified-since',utils.rfcDate(datetime.utcnow()))
    statusCode = utils.compareDate(ifmod,utils.rfcDate(dm),utils.rfcDate(datetime.utcnow()))
    statusCode = utils.compareDate2(ifunmod, utils.rfcDate(dm),statusCode)     
    with open(path,'rb') as f:
        f_bytes = f.read()
        
    extension = pathlib.Path(path).suffix
    subtype = extension[1:]  
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode': statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
        'responseHeaders': {
            'Connection' : 'close',
            'Date' : utils.rfcDate(datetime.utcnow()),
            'Last-Modified':utils.rfcDate(dm),
            
            "Set-Cookie": "yummy_cookie=choco"
        }, 
        'responseBody' : ''.encode()
    }
    if statusCode == '200':
        body = f_bytes
        if(contentencoding == 'gzip' or contentencoding == 'x-gzip'):
            body = gzip.compress(body)
        if(contentencoding == 'compress'):
            body = lzw3.compress(body)
        if(contentencoding == 'deflate'):
            body = zlib.compress(body)
        if(contentencoding == 'br'):
            body = brotli.compress(body)
        if contentencoding is not 'identity':
            responseDict['responseHeaders'].__setitem__('Content-Encoding',contentencoding)
        else:
            contentencoding = ""  
        responseDict.__setitem__('responseBody', body)
        responseDict['responseHeaders'].__setitem__('Content-Type' , typedict.get(subtype,'application/example'))
        responseDict['responseHeaders'].__setitem__('ETag','"{}"'.format(hashlib.md5((responseDict['responseHeaders']['Last-Modified'] + contentencoding).encode()).hexdigest()))
    return responseDict

def post(requestDict, *args):
    """
    The meaning of the Content-Location header in PUT or POST requests is
    undefined; servers are free to ignore it in those cases. (ignored)
    """
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    statusCode = None
    responseBody = ''
    with open('media-types/content-type-rev.json','r') as f:
        typeToExt = json.load(f) 
    contentEncoding = requestDict['requestHeaders'].get('content-encoding', '')
    contentEncoding = contentEncoding.split(',')
    contentType = requestDict['requestHeaders'].get('content-type', '')
    contentExt =  typeToExt.get(contentType, '')
    body = requestDict['requestBody']
    #decoding according to content-encoding
    if('content-md5' in requestDict['requestHeaders']):
        checksum = hashlib.md5(body).hexdigest()
        if(checksum != requestDict['requestHeaders']['content-md5']):
            statusCode = '400'
    if(not statusCode):
        for i in contentEncoding:
            i=i.strip()
            if(i == 'gzip' or i == 'x-gzip'):
                body = gzip.decompress(body)
            if(i == 'compress'):
                body = lzw3.decompress(body)
            if(i == 'deflate'):
                body = zlib.decompress(body)
            if(i == 'br'):
                body = brotli.decompress(body)
        #handling according to content-type
        statusCode = "200"
        if(contentExt=="x-www-form-urlencoded"):
            body = body.decode()
            queryDict = parse_qs(body, encoding='utf-8')
            queryWithDate = {utils.logDate(): queryDict}
            try:
                with open("log/postData.log", "a") as f:
                    json.dump(queryWithDate, f, indent="\t")
                    #log not exactly in json, but avoids reading overhead
                    f.write("\n")
                statusCode = "200"
                responseBody = "Data Logged"
            except:
                statusCode = "500"
        if(contentExt=="json"):
            body = body.decode()
            body = json.loads(body)
            queryWithDate = {utils.logDate(): body}
            try:
                with open("log/postData.log", "a") as f:
                    json.dump(queryWithDate, f, indent="\t")
                    #log not exactly in json, but avoids reading overhead
                    f.write("\n")
                statusCode = "200"
                responseBody = "Data Logged"
            except:
                statusCode = "500"
        else:
            try:
                queryWithDate = {utils.logDate(): body}
                with open("log/postData.log", "a") as f:
                    json.dump(queryWithDate, f, indent="\t")
                    f.write("\n")
                statusCode = "200"
                responseBody = "Data Logged"
            except:
                statusCode = "500"
    if(statusCode == "400"):
        responseDict = badRequest(requestDict, statusCode)
    else:
        responseDict = {
            'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
            'responseHeaders': {
                'Connection': 'close',
                'Date': utils.rfcDate(datetime.utcnow()),            
            },
            'responseBody' : responseBody.encode()
        }
    return responseDict

def put(requestDict, *args):
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    statusCode = None
    responseBody = ''
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    with open('media-types/content-type-rev.json','r') as f:
        typeToExt = json.load(f)
    requestLine = requestDict['requestLine']
    contentEncoding = requestDict['requestHeaders'].get('content-encoding', '')
    contentEncoding = contentEncoding.split(',')
    contentType = requestDict['requestHeaders'].get('content-type', '')
    contentExt =  typeToExt.get(contentType, '')
    requestBody = requestDict['requestBody']
    #decoding according to content-encoding
    if('content-md5' in requestDict['requestHeaders']):
        checksum = hashlib.md5(requestBody).hexdigest()
        if(checksum != requestDict['requestHeaders']['content-md5']):
            statusCode = '400'
    if(not statusCode):
        for i in contentEncoding:
            i=i.strip()
            if(i == 'gzip' or i == 'x-gzip'):
                requestBody = gzip.decompress(requestBody)
            if(i == 'compress'):
                requestBody = lzw3.decompress(requestBody)
            if(i == 'deflate'):
                requestBody = zlib.decompress(requestBody)
            if(i == 'br'):
                requestBody = brotli.decompress(requestBody)
        uri = requestLine['requestUri']
        uri = uri.lstrip('/')
        path = urlparse(uri).path
        path = path.lstrip('/')
        path = '/' + path
        # if path == '/':
        #     path = '/index.html'  
        path = config['DEFAULT']['DocumentRoot'] + path
        parentDirectory = os.path.split(path)[0]
        filename = os.path.split(path)[1]
        #create parent directory if does not exist
        if not os.path.exists(parentDirectory):
            os.makedirs(parentDirectory)
        try:
            if(os.path.exists(path)):
                statusCode = "200"
                responseBody = "Resource Modified"
            else:
                statusCode = "201"
                responseBody = "Resource Created"
            with open(path, "wb") as f:
                f.write(requestBody)
        except:
            statusCode = "500"
    # extension = pathlib.Path(path).suffix
    # subtype = extension[1:]  
    if(statusCode == "400"):
        responseDict = badRequest(requestDict, statusCode)
    else:
        responseDict = {
            'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode': statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
            'responseHeaders': {
                'Connection': 'close',
                'Date': utils.rfcDate(datetime.utcnow())
            },
            'responseBody' : responseBody.encode()
        }
    return responseDict    

def head(requestDict, *args):
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':'200', 'reasonPhrase':utils.givePhrase('200')},
        'responseHeaders': {
            'Connection': 'close',
            'Date': utils.rfcDate(datetime.utcnow()),            
        },
        'responseBody': "".encode()
    }
    return responseDict

def delete(requestDict, *args):
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    requestLine = requestDict['requestLine']
    # contentEncoding = requestDict['requestHeaders'].get('content-encoding', '')
    # contentEncoding = contentEncoding.split(',')
    # contentType = requestDict['requestHeaders'].get('content-type', '')
    # contentExt =  typeToExt.get(contentType, '')
    requestBody = requestDict['requestBody']
    uri = requestLine['requestUri']
    uri = uri.lstrip('/')
    path = urlparse(uri).path
    path = path.lstrip('/')
    path = '/' + path
    path = config['DEFAULT']['DocumentRoot'] + path
    if os.path.exists(path):
        try:
            os.remove(path)
        except IsADirectoryError:
            shutil.rmtree(path, ignore_errors=True)
        finally:
            statusCode = '200'
            responseBody = "Resource Deleted"
            responseDict = {
                'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
                'responseHeaders': {
                    'Connection': 'close',
                    'Date': utils.rfcDate(datetime.utcnow()),            
                },
                'responseBody': responseBody.encode()
            }
    else:
        responseDict = badRequest(requestDict, '404')

    return responseDict

#For handling all error status codes
def badRequest(requestDict, *args):
    statusCode = args[0]
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    with open('media-types/content-type.json','r') as jf:
        typedict = json.load(jf) 
    path = config['DEFAULT']['error-pages'] + f'/{statusCode}.html'
    extension = pathlib.Path(path).suffix
    subtype = extension[1:]
    f_bytes = b''
    if(os.path.exists(path)):
        with open(path,'rb') as f:
            f_bytes = f.read()
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
        'responseHeaders': {
            'Connection': 'close',
            'Date': utils.rfcDate(datetime.utcnow()),
            'Content-Type' : typedict.get(subtype,'application/example'),
            
            'Server': utils.getServerInfo()
        },
        'responseBody': f_bytes
    }
    if f_bytes is not b'':
        responseDict['responseHeaders'].__setitem__('Content-Length',str(len(f_bytes)))
    return responseDict
  