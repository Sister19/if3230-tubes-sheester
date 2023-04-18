import xmlrpc.client
import time
with xmlrpc.client.ServerProxy("http://localhost:8000/") as proxy:
    timee = time.time()
    
    print(proxy.ping())
    print("Elapsed time:", timee - time.time())
    timee = time.time()
    
    print(proxy.ping())
    print("Elapsed time:", timee - time.time())
    timee = time.time()
    
    print(proxy.ping())
    print("Elapsed time:", timee - time.time())
    timee = time.time()
    
    print(proxy.ping())
    print("Elapsed time:", timee - time.time())