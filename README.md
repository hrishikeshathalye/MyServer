<h1 align="center">MyServer</h1>

<div align="center">
  :globe_with_meridians:
</div>
<div align="center">
  <strong>A minimal, multithreaded HTTP/1.1 compliant Webserver</strong>
</div>
<br />

<div align="center">
  
 [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
 [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
 ![Version](https://img.shields.io/badge/version-1.0-blue])
</div>
  
<div align="center">
  <sub>Built by
  <a href="https://github.com/hrishikeshathalye">Hrishikesh Athalye</a> and
  <a href="https://github.com/shaunak27">Shaunak Halbe</a>  
</div>

## :dart: Table of Contents
- [Features](#features)
- [Usage](#usage)
- [Config](#config)
- [Testing](#testing)
- [Logs](#logs)
- [Acknowledgements](#config)

## :dart: Features
:heavy_check_mark: __Supports 5 common HTTP methods__ - GET, POST, PUT, DELETE and HEAD
:heavy_check_mark: __Multithreaded__
:heavy_check_mark: __Explicit configuration options__
:heavy_check_mark: __Level based logging support__
:heavy_check_mark: __Support for cookies__
:heavy_check_mark: __Automated basic testing__

## :dart: Usage
1. Install all required packages using "pip3 install -r requirements.txt"
2. Start the server using "python3 server.py port_no" , where port_no can be any valid port number. Not giving a port number will cause the server socket to bind to any available port. To bind to port numbers < 1024 prefixing the command with sudo is required.
3. To stop or restart the server just type "stop" or "restart" into the terminal window where the server is running and press enter. A thread that continuously keeps waiting for input takes this input and stops/restarts the server.
4. Server configuration options are available in the myserver.conf file in the conf directory.
5. Access Log, Error Log and Post Data Logs are located in the log directory. If not already present the server will create them.
(Being a general purpose web server, default behaviout for POST is to log POST data to PostDataLog.log)

## :dart: Config
Locate the file myserver.conf in the conf directory. The meanings of the various configuration options are as follows:

1. __DocumentRoot__ : The folder where get requests are served from and where PUT requests store data. The value against this filed will indicate the location of the document root relative to the working directory of the project.

2. __ErrorPages__ : Custom error pages can be put into this directory, error indicating status codes (Eg: 400, 404, etc) will be sent with body as pages put in this directory. If this directory does not contain status codes for some errors, a blank body will be sent for those.

3. __MaxSimultaneousConnections__ : Maximum number of connections that can be handled at once, connections more than this will queue and if queue size is full no connection can be made. If set to 1, the server will essentially behave like a single threaded server.

4. __QueueSize__ : The maximum number of connections that will be queued once maximum simultaenous connections have been reached

5. __RequestTimeout__ : Timeout for requests. Since the server is capable of handling requests made line-by-line (telnet like fashion), this indicates the maximum amount of time the server will wait before terminating the connection once inactivity is detected. The timer resets after each line typed by the client, if request is being made line-by-line. This ensures the server isn't being kept hanging by a client who has initiated a connection but is taking too long to request. 

6. __ServerCloseTimeout__ : Timeout to wait for requests to complete once a "stop" is given. If all requests are served before this timeout, server will stop immediately. else it will wait for a maximum time specified here, if requests do not complete within this time, the server still closes the connection immediately. This takes care of hanging threads and sets a hard limit on the timeout that the server will wait for.

7. __LogDir__ : Directory where log files are stored. (log by default)

8. __ErrorLog__ : Name of the error log file name. (error.log by default)

9. __AccessLog__ : Name of access log file name. (access.log by default)

10. __PostDataLog__ :  Name of file where log of POST data is stored. (postData.log by default)

11. __Log Level__ : Only errors of severity equal to and above this level will be logged into error.log. Can be one of - CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET (NOTSET by default)

## :dart: Testing
Run "python3 multithreadTest.py n" using the terminal where n specifies the number of stress test threads. Individual stress tests will spawn n threads to test each method.
Combination stress tests will spawn number of threads that approximately sum to n.
Do not start the server beforehand, the testing program will itself start the server before starting testing.

## :dart: Logs
__Log Formats:__

1. __Access Log__ :
<Ip-of-client> - - <date> <request-line> <response-status-code> <size-of-response-body-in-bytes> <referer> <user-agent> <value of set cookie header in response> <value of cookie header in request>

2. __Post Data Log__ : 
<datetime> - <post_data_as_bytestring>

## :dart: Acknowledgements
* [RFC 2616](https://tools.ietf.org/html/rfc2616)
* [RFC 6265](https://tools.ietf.org/html/rfc6265)
* [MDN HTTP Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP)
