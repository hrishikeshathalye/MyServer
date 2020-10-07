#module to handle all kinds of requests
import utils

#pass parsed request to these functions
#expect them to return the response fields as a dictionary
#call utils.responseBuilder in main

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
		

def get(requestDict):
    responseDict = {
        'statusLine': {'httpVersion':'HTTP/1.1', 'statusCode':'200', 'reasonPhrase':'OK'},
        'responseHeaders': {},
        'responseBody': "Hello World"
    }
    return responseDict

def post(requestDict):
    pass

def put(requestDict):
    pass

def head(requestDict):
    pass

def delete(requestDict):
    pass