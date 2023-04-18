import xmlrpc.client
import aioxmlrpc.client
import time
import asyncio
# task - asyncio

async def ping(port):
    time2 = time.time()
    proxy =  aioxmlrpc.client.ServerProxy(f"http://localhost:{port}/") 
    response = await proxy.ping()
    print(response)
    print("Elapsed time:", time.time() - time2)

async def main():
    await asyncio.gather(ping("8000"), ping("8001"))

if __name__ == '__main__':
    timee = time.time()
    asyncio.run(main())
    print("Elapsed time:", time.time() - timee)
