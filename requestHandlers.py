#module to handle all kinds of requests
import utils

#pass parsed request to these functions
#expect them to return the response fields as a dictionary
#call utils.responseBuilder in main

"""
general-header = 
    Cache-Control            ; Section 14.9
    Connection               ; Section 14.10
    Date                     ; Section 14.18
    Pragma                   ; Section 14.32
    Trailer                  ; Section 14.40
    Transfer-Encoding        ; Section 14.41
    Upgrade                  ; Section 14.42
    Via                      ; Section 14.45
    Warning                  ; Section 14.46
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
    Content-Encoding         ; Section 14.11
    Content-Language         ; Section 14.12
    Content-Length           ; Section 14.13
    Content-Location         ; Section 14.14
    Content-MD5              ; Section 14.15
    Content-Range            ; Section 14.16
    Content-Type             ; Section 14.17
    Expires                  ; Section 14.21
    Last-Modified            ; Section 14.29
    extension-header
"""
		

def get(requestDict):
    # relUrl = requestDict['requestLine']['requestUri'].split('/', 1)
    # relUrl = relUrl[1]
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':'200', 'reasonPhrase':utils.givePhrase('200')},
        'responseHeaders': {},
        'responseBody': "Hello World\n"
    }
    return responseDict

def post(requestDict):
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':'200', 'reasonPhrase':utils.givePhrase('200')},
        'responseHeaders': {
            'Connection': 'close',
            'Date': utils.rfcDate(),         
        },
        'responseBody': ""
    }
    return responseDict

def put(requestDict):
    pass

def head(requestDict):
    pass

def delete(requestDict):
    pass

def other(requestDict):
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':'501', 'reasonPhrase':utils.givePhrase('501')},
        'responseHeaders': {},
        'responseBody': ""
    }
    return responseDict