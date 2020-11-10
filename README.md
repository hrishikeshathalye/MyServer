# Multithreaded Web Server
<h5>Team Members:</h5>

1. 111803154 - Hrishikesh Athalye - TY Comp Div 2
2. 111803053 - Shaunak Halbe - TY Comp Div 1

Implementation of a multithreaded http server for Computer Networks course.

Steps to run the project :

1. Install all required packages using "pip install -r requirements.txt"
2. Start the server using "sudo python3 server.py port_no" , where port_no can be any valid port number. Not giving a port number will cause the server socket to bind to any available port.
3. To stop or restart the server just type "stop" or "restart" into the terminal window where the server is running and press enter. A thread that contiuously keeps waiting for input takes this input and stops/restarts the server.

Steps to run the test :

1. Run "sudo python3 multithreadTest.py n" using the terminal where n specifies the number of stress test threads. Individual stress tests will spawn n threads to test each method.
Combination stress tests will spawn number of threads that approximately sum to n.
Do not start the server beforehand, the testing program will itself start the server before starting testing.

