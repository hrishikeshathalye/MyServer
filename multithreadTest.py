import json
import threading
import time
import unittest
import requests

from server import Server

SERVER_URL = "http://127.0.0.1:90"

server = Server('', 90)
server_thread = threading.Thread(target=server.serve)
server_thread.start()

#GET Request
class test_1(unittest.TestCase):
    """A Test case to test GET Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 GET Request Threads")

        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:
            def get_test():
                r = requests.get(SERVER_URL + "/",)
                #will uncomment below line for verbose command line option
                # print(f"{r.status_code} {r.reason}, Time Elapsed : {r.elapsed}")
            
            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=get_test)
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
    """A Test case to test POST Request"""
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
                r = requests.post(SERVER_URL + "/test",
                    data=json.dumps(data),
                    headers={'content-type': 'application/json'}
                )
                # print(f"{r.status_code} {r.reason}, Time Elapsed : {r.elapsed}")
            
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
    """A Test case to test HEAD Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 HEAD Request Threads")
        
        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:

            def head_test():
                r = requests.head(SERVER_URL + "/")
                # print(f"{r.status_code} {r.reason}, Time Elapsed : {r.elapsed}")
            
            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=head_test)
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
    """A Test case to test PUT Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 PUT Request Threads")

        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:
            def put_test(fileno):
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )

                r = requests.put(SERVER_URL + f"/test/test{fileno}.json",
                    data=json.dumps(data),
                    headers={'content-type': 'application/json'}
                )
                # print(f"{r.status_code} {r.reason}, Time Elapsed : {r.elapsed}")
            
            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=put_test, args=(i+1,))
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
    """A Test case to test DELETE Request"""
    def runTest(self):
        """Running Test"""
        print("\nDispatching 100 DELETE Request Threads")
        # Create a thread that will contain our running server

        # The number of client threads to create
        n_clientThreads = 100

        request_threads = []
        try:
            def delete_test(fileno):
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                # Make the actual request making sure that we pass the data,
                # the appropriate headers, and the cookies that were passed
                # use during the login phase
                r = requests.delete(SERVER_URL + f"/test/test{fileno}.json")
                # print(f"{r.status_code} {r.reason}, Time Elapsed : {r.elapsed}")

            # Create threads for all of the requests and start them
            for i in range(n_clientThreads):
                t = threading.Thread(target=delete_test, args=(i+1,))
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