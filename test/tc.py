import xmlrpc.client
import aioxmlrpc.client
import aiohttp
import aiohttp_xmlrpc.client

from aiohttp_xmlrpc.client import ClientPool
import time
import asyncio
# task - asyncio

async def ping(port):
    time2 = time.time()
    try:
        proxy = aiohttp_xmlrpc.client.ServerProxy(f"http://localhost:{port}/")
        response = await proxy.ping()
        await proxy.close()
        print(response)

    aiohttp_xmlrpc.client.Cl


    except Exception as e:
        print(e)
    print("Elapsed time:", time.time() - time2)

async def main():
    await asyncio.gather(ping("8000"), ping("8001"))

if __name__ == '__main__':
    timee = time.time()
    asyncio.run(main())
    print("Elapsed time:", time.time() - timee)
