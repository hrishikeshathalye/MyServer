import json
import threading
import time
import unittest
import requests
import random
import sys

from server import Server

SERVER_URL = "http://127.0.0.1:90"

server = Server('', 90)
server_thread = threading.Thread(target=server.serve)
server_thread.start()
n_clientThreads = 1

#GET Request
class test_01(unittest.TestCase):
    """CONFORMANCE TEST - Testing GET Request"""
    def runTest(self):
        """CONFORMANCE TEST - Testing GET"""
        print("\nMaking a GET Request")
        try:
            r = requests.get(SERVER_URL + "/")
            print(f"Status : {r.status_code} {r.reason}")
            print("Headers:", r.headers)
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            # Stop all running threads
            return
class test_02(unittest.TestCase):
    """CONFORMANCE TEST - Testing Conditional GET Request"""
    def runTest(self):
        """CONFORMANCE TEST - Testing Conditional GET"""
        print("\nMaking a Normal GET Request")
        try:
            headers = dict()
            r = requests.get(SERVER_URL + "/")
            print(f"Status : {r.status_code} {r.reason}")
            lastModified = r.headers['Last-Modified']
            headers['If-Modified-Since'] = lastModified
            print(f"Last Modified Date Obtained : {lastModified}")
            print(f"Sending a conditional GET with the If-Mod-Since same as Last-Modified")
            r = requests.get(SERVER_URL + "/", headers=headers)
            print(f"Status : {r.status_code} {r.reason}")
            print(f"Sending a conditional GET with the If-Mod-Since older than Last-Modified")
            headers['If-Modified-Since'] = "Tue, 27 Oct 1999 08:57:08 GMT"
            r = requests.get(SERVER_URL + "/", headers=headers)
            print(f"Status : {r.status_code} {r.reason}")
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            # Stop all running threads
            return
class test_03(unittest.TestCase):
    """CONFORMANCE TEST - Testing POST Request"""
    def runTest(self):
        """CONFORMANCE TEST - Testing POST Request"""
        try:
            print("\nMaking a POST Request")
            data = dict(
                key1='TEST',
                value1='TEST DATA'
            )
            r = requests.post(SERVER_URL + "/test",
                data=json.dumps(data),
                headers={'content-type': 'application/json'}
            )
            print(f"Status : {r.status_code} {r.reason}")
            print("Headers:", r.headers)
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            return

class test_04(unittest.TestCase):
    """CONFORMANCE TEST - Testing HEAD Request"""
    def runTest(self):
        """CONFORMANCE TEST - Testing HEAD Request"""
        print("\nMaking a HEAD Request")
        try:
            r = requests.head(SERVER_URL + "/")
            print(f"Status : {r.status_code} {r.reason}")
            print("Headers:", r.headers)
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            return

class test_05(unittest.TestCase):
    """CONFORMANCE TEST - Testing PUT Request"""
    def runTest(self):
        """CONFORMANCE TEST - Testing PUT Request"""
        print("\nMaking a PUT Request")
        try:
            data = dict(
                key1='TEST',
                value1='TEST DATA'
            )
            r = requests.put(SERVER_URL + f"/test/test{1}.json",
                data=json.dumps(data),
                headers={'content-type': 'application/json'}
            )
            print(f"Status : {r.status_code} {r.reason}")
            print("Headers:", r.headers)
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            return

class test_06(unittest.TestCase):
    """CONFORMANCE TEST - Testing DELETE Request"""
    def runTest(self):
        """CONFORMANCE TEST - Testing DELETE Request"""
        print("\nMaking a DELETE Request")
        try:
            data = dict(
                key1='TEST',
                value1='TEST DATA'
            )
            r = requests.delete(SERVER_URL + f"/test/test{1}.json")
            print(f"Status : {r.status_code} {r.reason}")
            print("Headers:", r.headers)
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            return

class test_07(unittest.TestCase):
    """CONFORMANCE TEST - Cookies"""
    def runTest(self):
        """Testing Cookies"""
        try:
            print("\nCreating a cookie store...")
            session = requests.Session()
            print("Content in cookie store before request:")
            print(session.cookies.get_dict())
            print("Making 1st GET Request...")
            response = session.get(SERVER_URL + "/")
            print("Content in cookie store after request:")
            print(session.cookies.get_dict())
            print("Making 2nd GET Request... (Cookie returned should now be same)")
            response = session.get(SERVER_URL + "/")
            print("Content in cookie store after 2nd request:")
            print(session.cookies.get_dict())
            print("Clearing cookie store...")
            session.cookies.clear()
            print("Making 3rd GET Request... (Cookie returned should now be a new unique cookie since cookie store is empty)")
            response = session.get(SERVER_URL + "/")
            print("Content in cookie store after 3rd request:")
            print(session.cookies.get_dict())
        except Exception as ex:
            print('Something went horribly wrong!', ex)
        finally:
            return

class test_08(unittest.TestCase):
    """STRESS TEST - GET Request"""
    def runTest(self):
        """STRESS TEST - GET Request"""

        print(f"\nDispatching {n_clientThreads} GET Request Threads")

        request_threads = []
        try:
            def get_test():
                try:
                    r = requests.get(SERVER_URL + "/")
                    #will uncomment below line for verbose command line option
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")
            
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
class test_09(unittest.TestCase):
    """STRESS TEST - POST Request"""
    def runTest(self):
        """STRESS TEST - POST Request"""

        print(f"\nDispatching {n_clientThreads} POST Request Threads")

        request_threads = []
        try:
            def post_test():
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                try:
                    r = requests.post(SERVER_URL + "/test",
                        data=json.dumps(data),
                        headers={'content-type': 'application/json'}
                    )
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")
            
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

class test_10(unittest.TestCase):
    """STRESS TEST - HEAD Request"""
    def runTest(self):
        """STRESS TEST - HEAD Request"""

        print(f"\nDispatching {n_clientThreads} HEAD Request Threads")
        request_threads = []
        try:

            def head_test():
                try:
                    r = requests.head(SERVER_URL + "/")
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")         
            
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

class test_11(unittest.TestCase):
    """STRESS TEST - PUT Request"""
    def runTest(self):
        """STRESS TEST - PUT Request"""

        print(f"\nDispatching {n_clientThreads} PUT Request Threads")

        request_threads = []
        try:
            def put_test(fileno):
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                try:
                    r = requests.put(SERVER_URL + f"/test/test{fileno}.json",
                        data=json.dumps(data),
                        headers={'content-type': 'application/json'}
                    )
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")
            
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

class test_12(unittest.TestCase):
    """STRESS TEST - DELETE Request"""
    def runTest(self):
        """STRESS TEST - DELETE Request"""
        print(f"\nDispatching {n_clientThreads} DELETE Request Threads")
        request_threads = []
        try:
            def delete_test(fileno):
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                try:
                    r = requests.delete(SERVER_URL + f"/test/test{fileno}.json")
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")

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

class test_13(unittest.TestCase):
    """STRESS TEST - Random Request Combination"""
    def runTest(self):
        """STRESS TEST - Random Request Combination"""
        sample = random.sample(range(n_clientThreads), 5)
        s = sum(sample)
        numRequests = [(i*n_clientThreads)//s for i in sample]
        # The number of client threads to create
        getThreads = numRequests[0]
        headThreads = numRequests[1]
        postThreads = numRequests[2]
        putThreads = numRequests[3]
        deleteThreads = numRequests[4]
        print(f"\nDispatching {getThreads} GET, {headThreads} HEAD, {postThreads} POST, {putThreads} PUT, {deleteThreads} DELETE request threads")
        request_threads = []
        try:
            def get_test():
                try:
                    r = requests.get(SERVER_URL + "/")
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")
            def head_test():
                try:
                    r = requests.head(SERVER_URL + "/")
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")
            def post_test():
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                try:
                    r = requests.post(SERVER_URL + "/test",
                        data=json.dumps(data),
                        headers={'content-type': 'application/json'}
                    )
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")
            def put_test(fileno):
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                try:
                    r = requests.put(SERVER_URL + f"/test/test{fileno}.json",
                        data=json.dumps(data),
                        headers={'content-type': 'application/json'}
                    )
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")
            def delete_test(fileno):
                data = dict(
                    key1='TEST',
                    value1='TEST DATA'
                )
                try:
                    r = requests.delete(SERVER_URL + f"/test/test{fileno}.json")
                    # print(f"Status : {r.status_code} {r.reason}")
                except:
                    print("Error in making request, maybe server queue is full")

            # Create threads for all of the requests and start them
            for i in range(getThreads):
                t = threading.Thread(target=get_test)
                request_threads.append(t)
                t.start()
            # for i in range(headThreads):
            #     t = threading.Thread(target=head_test)
            #     request_threads.append(t)
            #     t.start()
            for i in range(postThreads):
                t = threading.Thread(target=post_test)
                request_threads.append(t)
                t.start()
            for i in range(putThreads):
                t = threading.Thread(target=put_test, args=(i+1,))
                request_threads.append(t)
                t.start()
            for i in range(deleteThreads):
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
class test_14(unittest.TestCase):
    def runTest(self):
        """Testing server stopping"""
        print("")
        server.stop()

if __name__ == '__main__':
    #accepting stress testing parameters as command line arguments
    n_clientThreads = int(sys.argv[1])
    unittest.main(verbosity=2, argv=[sys.argv[0]])
