import json
import threading
import time
import unittest
import requests
from hanging_threads import start_monitoring

from server import Server

SERVER_URL = "http://127.0.0.1:90"

server = Server('', 90)
server_thread = threading.Thread(target=server.serve)
server_thread.start()

#GET Request
class test_1(unittest.TestCase):
    """A Test case to test post Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 GET Request Threads")
        # Create a thread that will contain our running server
        

        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:
            def post_test():
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                # Make the actual request making sure that we pass the data,
                # the appropriate headers, and the cookies that were passed
                # use during the login phase
                r = requests.post(SERVER_URL + "/test",
                                data=json.dumps(data),
                                headers={'content-type': 'application/json'}
                                )
            
            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=post_test)
                request_threads.append(t)
                t.start()

            # Wait until all of the threads are complete
            for thread in request_threads:
                thread.join()
            
            # print("All GET Requests Complete")
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            # Stop all running threads
            return

#POST Request
class test_2(unittest.TestCase):
    """A Test case to test post Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 POST Request Threads")

        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:
            def post_test():
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                # Make the actual request making sure that we pass the data,
                # the appropriate headers, and the cookies that were passed
                # use during the login phase
                r = requests.post(SERVER_URL + "/test",
                                data=json.dumps(data),
                                headers={'content-type': 'application/json'}
                                )
            
            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=post_test)
                request_threads.append(t)
                t.start()

            # Wait until all of the threads are complete
            for thread in request_threads:
                thread.join()
            
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            # Stop all running threads
            return

class test_3(unittest.TestCase):
    """A Test case to test post Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 HEAD Request Threads")
        # Create a thread that will contain our running server

        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:

            def post_test():
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                # Make the actual request making sure that we pass the data,
                # the appropriate headers, and the cookies that were passed
                # use during the login phase
                r = requests.post(SERVER_URL + "/test",
                                data=json.dumps(data),
                                headers={'content-type': 'application/json'}
                                )
            
            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=post_test)
                request_threads.append(t)
                t.start()

            # Wait until all of the threads are complete
            for thread in request_threads:
                thread.join()
            
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            # Stop all running threads
            return

class test_4(unittest.TestCase):
    """A Test case to test post Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 PUT Request Threads")
        # Create a thread that will contain our running server

        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:
            def post_test():
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                # Make the actual request making sure that we pass the data,
                # the appropriate headers, and the cookies that were passed
                # use during the login phase
                r = requests.post(SERVER_URL + "/test",
                                data=json.dumps(data),
                                headers={'content-type': 'application/json'}
                                )
            
            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=post_test)
                request_threads.append(t)
                t.start()

            # Wait until all of the threads are complete
            for thread in request_threads:
                thread.join()
            
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            # Stop all running threads
            return

class test_5(unittest.TestCase):
    """A Test case to test post Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 DELETE Request Threads")
        # Create a thread that will contain our running server

        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:
            def post_test():
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                # Make the actual request making sure that we pass the data,
                # the appropriate headers, and the cookies that were passed
                # use during the login phase
                r = requests.post(SERVER_URL + "/test",
                                data=json.dumps(data),
                                headers={'content-type': 'application/json'}
                                )
            
            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=post_test)
                request_threads.append(t)
                t.start()

            # Wait until all of the threads are complete
            for thread in request_threads:
                thread.join()
            
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            # Stop all running threads
            return

#testing server close
class test_6(unittest.TestCase):
    def runTest(self):
        print("")
        server.stop()

if __name__ == '__main__':
    unittest.main(verbosity=2)
    