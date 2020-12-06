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

def get(requestDict, *args):
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    if('host' not in requestDict['requestHeaders']):
        return badRequest(requestDict, '400')
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    ipaddress = args[1]
    requestLine = requestDict['requestLine']
    requestHeaders = requestDict['requestHeaders']
    acceptencoding = requestHeaders.get('accept-encoding',"")
    accept = requestHeaders.get('accept','*/*')
    contentencoding = utils.prioritizeEncoding(acceptencoding)
    ce = contentencoding
    statusCode = '200'
    if contentencoding == 'identity':
        ce = ""
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
    extension = pathlib.Path(path).suffix      
    subtype = utils.prioritizeMedia(accept,extension,path)
    if subtype == -1 :
        return badRequest(requestDict,'406',0)
    if subtype == "*":
        subtype = extension[1:]   
    # path = path.rstrip(pathlib.Path(path).suffix) + "." + subtype    
    path = path.strip().split(pathlib.Path(path).suffix, 1)[0] + "." + subtype    
    dm = datetime.fromtimestamp(mktime(time.gmtime(os.path.getmtime(path))))
    ifmod = requestHeaders.get('if-modified-since',utils.rfcDate(datetime.fromtimestamp(0)))         
    ifunmod = requestHeaders.get('if-unmodified-since',utils.rfcDate(datetime.utcnow()))
    ifmatch = requestHeaders.get('if-match',"*")
    ifnonematch = requestHeaders.get('if-none-match',"")
    ifmatchlist = utils.ifmatchparser(ifmatch)
    ifnmatchlist = utils.ifmatchparser(ifnonematch)
    Etag =  '"{}"'.format(hashlib.md5((utils.rfcDate(dm) + ce).encode()).hexdigest())
    for iftag in ifmatchlist:
        if iftag == "*" or Etag == iftag:
            break
    else:
        statusCode = '412'  
    for ifntag in ifnmatchlist:
        if ifntag == "*" or Etag == ifntag:
            statusCode = '304'
            break 
        elif ifntag == "":
            break    
    else: 
        ifmod = utils.rfcDate(datetime.fromtimestamp(0))    
    if ifmod == utils.rfcDate(datetime.fromtimestamp(0)):
        flag = 1 
    else :
        flag = 0               
    statusCode = utils.compareDate(ifmod,utils.rfcDate(dm),utils.rfcDate(datetime.utcnow()),statusCode,flag)
    statusCode = utils.compareDate2(ifunmod, utils.rfcDate(dm),statusCode)           
    try:
        with open(path,'rb') as f:
            f_bytes = f.read()
    except PermissionError:
        return badRequest(requestDict, '403')
    try:
        cookie = utils.parsecookie(requestHeaders['cookie'])    
    except:
        cookie = utils.makecookie(path,ipaddress,utils.rfcDate(datetime.utcnow()))    
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode': statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
        'responseHeaders': {
            'Connection' : 'close',
            'Date' : utils.rfcDate(datetime.utcnow()),
            'Last-Modified':utils.rfcDate(dm),
            'Server': utils.getServerInfo()
        }, 
        'responseBody' : ''.encode()
    }
    for i in cookie.keys():
        responseDict['responseHeaders'].__setitem__('Set-Cookie',i + '=' + cookie[i])
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
        if contentencoding != 'identity':
            responseDict['responseHeaders'].__setitem__('Content-Encoding',contentencoding)
        else:
            contentencoding = ""  
        responseDict.__setitem__('responseBody', body)
        responseDict['responseHeaders'].__setitem__('Content-Length',str(len(body)))
        responseDict['responseHeaders'].__setitem__('Content-Type' , typedict.get(subtype,'application/example'))
        responseDict['responseHeaders'].__setitem__('ETag',Etag)
    return responseDict

def post(requestDict, *args):
    """
    The meaning of the Content-Location header in PUT or POST requests is
    undefined; servers are free to ignore it in those cases. (ignored)
    """
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    if('host' not in requestDict['requestHeaders']):
        return badRequest(requestDict, '400')
    requestHeaders = requestDict['requestHeaders']
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    ipaddress = args[1]
    postDataLogPath = os.path.join(config['DEFAULT']['LogDir'], config['DEFAULT']['PostDataLog'])
    dm = datetime.fromtimestamp(mktime(time.gmtime(os.path.getmtime(postDataLogPath))))
    ifmatch = requestHeaders.get('if-match',"*")  
    ifmatchlist = utils.ifmatchparser(ifmatch)
    Etag =  '"{}"'.format(hashlib.md5((utils.rfcDate(dm)).encode()).hexdigest())
    for iftag in ifmatchlist:
        if iftag == "*" or Etag == iftag:
            break
    else:
        return badRequest(requestDict, '412')
    statusCode = None
    responseBody = ''
    with open('media-types/content-type-rev.json','r') as f:
        typeToExt = json.load(f) 
    contentEncoding = requestDict['requestHeaders'].get('content-encoding', '')
    contentEncoding = contentEncoding.split(',')
    contentType = requestDict['requestHeaders'].get('content-type', '')
    contentExt =  typeToExt.get(contentType, '')
    body = requestDict['requestBody']
    try:
        cookie = utils.parsecookie(requestHeaders['cookie'])    
    except:
        cookie = utils.makecookie('/',ipaddress,utils.rfcDate(datetime.utcnow()))   
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
                with open(postDataLogPath, "a") as f:
                    json.dump(queryWithDate, f, indent="\t")
                    #log not exactly in json, but avoids reading overhead
                    f.write("\n")
                statusCode = "200"
                responseBody = "Data Logged"
            except PermissionError:
                return badRequest(requestDict, '403')
            except:
                statusCode = "500"
        elif(contentExt=="json"):
            body = body.decode()
            body = json.loads(body)
            queryWithDate = {utils.logDate(): body}
            try:
                with open(postDataLogPath, "a") as f:
                    json.dump(queryWithDate, f, indent="\t")
                    #log not exactly in json, but avoids reading overhead
                    f.write("\n")
                statusCode = "200"
                responseBody = "Data Logged"
            except PermissionError:
                return badRequest(requestDict, '403')
            except:
                statusCode = "500"
        else:
            try:
                queryWithDate = {utils.logDate(): body}
                with open(postDataLogPath, "a") as f:
                    json.dump(queryWithDate, f, indent="\t")
                    f.write("\n")
                statusCode = "200"
                responseBody = "Data Logged"
            except PermissionError:
                return badRequest(requestDict, '403')
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
                'Server': utils.getServerInfo()  ,
                'ETag' : Etag        
            },
            'responseBody' : responseBody.encode()
        }
        responseDict['responseHeaders'].__setitem__('Content-Length',str(len(responseDict['responseBody'])))
        for i in cookie.keys():
            responseDict['responseHeaders'].__setitem__('Set-Cookie',i + '=' + cookie[i])
    return responseDict

def put(requestDict, *args):
    requestHeaders = requestDict['requestHeaders']
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    if('host' not in requestDict['requestHeaders']):
        return badRequest(requestDict, '400')
    statusCode = None
    ipaddress = args[1]
    responseBody = ''
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    with open('media-types/content-type-rev.json','r') as f:
        typeToExt = json.load(f)
    requestLine = requestDict['requestLine']
    contentEncoding = requestDict['requestHeaders'].get('content-encoding', '')
    contentEncoding = contentEncoding.split(',')
    contentType = requestDict['requestHeaders'].get('content-type', '-')
    contentExt =  typeToExt.get(contentType, '-')
    requestBody = requestDict['requestBody']
    uri = requestLine['requestUri']
    uri = uri.lstrip('/')
    path = urlparse(uri).path
    path = path.lstrip('/')
    path = '/' + path
    if(contentExt!='-'):
        tmp = path.rsplit('.', 1)[0]
        path = tmp+f'.{contentExt}'
    # if path == '/':
    #     path = '/index.html'  
    path = config['DEFAULT']['DocumentRoot'] + path
    Etag = None
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
        
        parentDirectory = os.path.split(path)[0]
        filename = os.path.split(path)[1]
        try:
            cookie = utils.parsecookie(requestHeaders['cookie'])    
        except:
            cookie = utils.makecookie(path,ipaddress,utils.rfcDate(datetime.utcnow())) 
        #create parent directory if does not exist
        if not os.path.exists(parentDirectory):
            os.makedirs(parentDirectory)
        try:
            if(os.path.exists(path)):
                dm = datetime.fromtimestamp(mktime(time.gmtime(os.path.getmtime(path))))
                ifmatch = requestHeaders.get('if-match',"*")  
                ifmatchlist = utils.ifmatchparser(ifmatch)
                Etag =  '"{}"'.format(hashlib.md5((utils.rfcDate(dm) + contentEncoding[0]).encode()).hexdigest())
                for iftag in ifmatchlist:
                    if iftag == "*" or Etag == iftag:
                        break
                    else:
                        statusCode = '412'
                if(statusCode!='412'):
                    statusCode = "200"
                    responseBody = "Resource Modified"
            else:
                statusCode = "201"
                responseBody = "Resource Created"
            with open(path, "wb") as f:
                if(statusCode!='412'):
                    f.write(requestBody)
        except PermissionError:
            return badRequest(requestDict, '403')
        except:
            statusCode = "500"
            responseBody = ""
    # extension = pathlib.Path(path).suffix
    # subtype = extension[1:]  
    if(statusCode == "400"):
        responseDict = badRequest(requestDict, statusCode)
    elif(statusCode == "412"):
        responseDict = badRequest(requestDict, statusCode)
    else:
        responseDict = {
            'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode': statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
            'responseHeaders': {
                'Connection': 'close',
                'Date': utils.rfcDate(datetime.utcnow()),
                'Server': utils.getServerInfo()
            },
            'responseBody' : responseBody.encode()
        }
        responseDict['responseHeaders'].__setitem__('Content-Length',str(len(responseDict['responseBody'])))
        if Etag:
            responseDict['responseHeaders'].__setitem__('ETag',Etag)
        for i in cookie.keys():
            responseDict['responseHeaders'].__setitem__('Set-Cookie',i + '=' + cookie[i])
    return responseDict    

def head(requestDict, *args):
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505',0)
    if('host' not in requestDict['requestHeaders']):
        return badRequest(requestDict, '400',0)
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    ipaddress = args[1]
    requestLine = requestDict['requestLine']
    requestHeaders = requestDict['requestHeaders']
    acceptencoding = requestHeaders.get('accept-encoding',"")
    accept = requestHeaders.get('accept','*/*')
    contentencoding = utils.prioritizeEncoding(acceptencoding)
    ce = contentencoding
    statusCode = '200'
    if contentencoding == 'identity':
        ce = ""
    if not contentencoding:
        return badRequest(requestDict, '406',0)
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
        return badRequest(requestDict, '404',0)
    extension = pathlib.Path(path).suffix      
    subtype = utils.prioritizeMedia(accept,extension,path)
    if subtype == -1 :
        return badRequest(requestDict,'406',0)
    if subtype == "*":
        subtype = extension[1:]   
    path = path.rstrip(pathlib.Path(path).suffix) + "." + subtype    
    dm = datetime.fromtimestamp(mktime(time.gmtime(os.path.getmtime(path))))
    ifmod = requestHeaders.get('if-modified-since',utils.rfcDate(datetime.fromtimestamp(0)))         
    ifunmod = requestHeaders.get('if-unmodified-since',utils.rfcDate(datetime.utcnow()))
    ifmatch = requestHeaders.get('if-match',"*")
    ifnonematch = requestHeaders.get('if-none-match',"")
    ifmatchlist = utils.ifmatchparser(ifmatch)
    ifnmatchlist = utils.ifmatchparser(ifnonematch)
    Etag =  '"{}"'.format(hashlib.md5((utils.rfcDate(dm) + ce).encode()).hexdigest())
    for iftag in ifmatchlist:
        if iftag == "*" or Etag == iftag:
            break
    else:
        statusCode = '412'  
    for ifntag in ifnmatchlist:
        if ifntag == "*" or Etag == ifntag:
            statusCode = '304'
            break 
        elif ifntag == "":
            break    
    else: 
        ifmod = utils.rfcDate(datetime.fromtimestamp(0))    
    if ifmod == utils.rfcDate(datetime.fromtimestamp(0)):
        flag = 1 
    else :
        flag = 0               
    statusCode = utils.compareDate(ifmod,utils.rfcDate(dm),utils.rfcDate(datetime.utcnow()),statusCode,flag)
    statusCode = utils.compareDate2(ifunmod, utils.rfcDate(dm),statusCode)           
    try:
        with open(path,'rb') as f:
            f_bytes = f.read()
    except PermissionError:
        return badRequest(requestDict, '403',0)
    try:
        cookie = utils.parsecookie(requestHeaders['cookie'])    
    except:
        cookie = utils.makecookie(path,ipaddress,utils.rfcDate(datetime.utcnow()))    
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode': statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
        'responseHeaders': {
            'Connection' : 'close',
            'Date' : utils.rfcDate(datetime.utcnow()),
            'Last-Modified':utils.rfcDate(dm),
            'Server': utils.getServerInfo()
        }, 
        'responseBody' : ''.encode()
    }
    for i in cookie.keys():
        responseDict['responseHeaders'].__setitem__('Set-Cookie',i + '=' + cookie[i])
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
        if contentencoding != 'identity':
            responseDict['responseHeaders'].__setitem__('Content-Encoding',contentencoding)
        else:
            contentencoding = ""  
        responseDict['responseHeaders'].__setitem__('Content-Length',str(len(body)))
        responseDict['responseHeaders'].__setitem__('Content-Type' , typedict.get(subtype,'application/example'))
        responseDict['responseHeaders'].__setitem__('ETag',Etag)
    return responseDict

def delete(requestDict, *args):
    if(not utils.compatCheck(requestDict['requestLine']['httpVersion'])):
        return badRequest(requestDict, '505')
    if('host' not in requestDict['requestHeaders']):
        return badRequest(requestDict, '400')
    requestHeaders = requestDict['requestHeaders']
    ipaddress = args[1]    
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    requestLine = requestDict['requestLine']
    requestBody = requestDict['requestBody']
    uri = requestLine['requestUri']
    uri = uri.lstrip('/')
    path = urlparse(uri).path
    path = path.lstrip('/')
    path = '/' + path
    path = config['DEFAULT']['DocumentRoot'] + path
    Etag = None
    try:
        cookie = utils.parsecookie(requestHeaders['cookie'])    
    except:
        cookie = utils.makecookie(path,ipaddress,utils.rfcDate(datetime.utcnow()))   
    if os.path.exists(path):
        try:
            dm = datetime.fromtimestamp(mktime(time.gmtime(os.path.getmtime(path))))
            ifmatch = requestHeaders.get('if-match',"*")  
            ifmatchlist = utils.ifmatchparser(ifmatch)
            Etag =  '"{}"'.format(hashlib.md5((utils.rfcDate(dm)).encode()).hexdigest())
            for iftag in ifmatchlist:
                if iftag == "*" or Etag == iftag:
                    break
            else:
                return badRequest(requestDict, '412')
            try:
                os.remove(path)
            except PermissionError:
                return badRequest(requestDict, '403')
        except IsADirectoryError:
            try:
                shutil.rmtree(path, ignore_errors=True)
            except PermissionError:
                return badRequest(requestDict, '403')
        finally:
            statusCode = '200'
            responseBody = "Resource Deleted"
            responseDict = {
                'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':statusCode, 'reasonPhrase':utils.givePhrase(statusCode)},
                'responseHeaders': {
                    'Connection': 'close',
                    'Date': utils.rfcDate(datetime.utcnow()), 
                    'Server': utils.getServerInfo()                          
                },
                'responseBody': responseBody.encode()
            }
            responseDict['responseHeaders'].__setitem__('Content-Length',str(len(responseDict['responseBody'])))
            if Etag:
                responseDict['responseHeaders'].__setitem__('ETag',Etag)
            for i in cookie.keys():
                responseDict['responseHeaders'].__setitem__('Set-Cookie',i + '=' + cookie[i])
    else:
        responseDict = badRequest(requestDict, '404')

    return responseDict

#For handling all error status codes
def badRequest(requestDict, statusCode, isnhead = 1):
    config = configparser.ConfigParser()
    config.read('conf/myserver.conf')
    with open('media-types/content-type.json','r') as jf:
        typedict = json.load(jf) 
    path = config['DEFAULT']['ErrorPages'] + f'/{statusCode}.html'
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
            'Server': utils.getServerInfo(),
        },
        'responseBody' : ''.encode()
    }
    if f_bytes != b'' and isnhead:
        responseDict.__setitem__('responseBody', f_bytes)
        responseDict['responseHeaders'].__setitem__('Content-Type' , typedict.get(subtype,'application/example'))
    responseDict['responseHeaders'].__setitem__('Content-Length',str(len(responseDict['responseBody'])))    
    return responseDict
  