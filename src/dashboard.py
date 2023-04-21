#flask
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from lib.struct.address import Address
import asyncio
import aiohttp_xmlrpc.client
import json
import threading
import time

app = Flask(__name__)
cluster_addr_list = [Address("localhost",12000)]
nodes_data = []

async def __send_aio_request(addr: Address):        
        #NON BLOCKING
        node = None
        try:
            node = aiohttp_xmlrpc.client.ServerProxy(f"http://{addr.ip}:{addr.port}") #this library doesnt have timeouts?
            # client._transport.timeout = RaftNode.RPC_TIMEOUT 
            response     =  json.loads(await node.get_dashboard_data())
            return response
        
        except Exception as e:
            print("Exception:", str(e))

            return "error"
        finally:
            if node is not None:
                await node.close()
        # return json.loads(result)


async def getData():
    global nodes_data 
    global cluster_addr_list
    nodes_data= []
    try:
        tasks=[]
        address_list_copy = []
        for address in cluster_addr_list:
            address_list_copy.append(address)
            task = asyncio.create_task(__send_aio_request(address))
            tasks.append(task)
        
        # await asyncio.gather(*tasks)
        if(tasks):
            done, _ = await asyncio.wait(tasks,timeout = 10)
            
            for task in done:
                try:
                    result = await task
                    # print("Result" , result)
                    if(result == "error"):
                        continue

                    if(result["type"] == 1):
                        cluster_addr_list = []
                        for d in result["cluster_addr_list"]:   #turn json dicts back into address
                            address = Address(d["ip"], d["port"])
                            cluster_addr_list.append(address)

                    ip = result["address"]["ip"]
                    port = result["address"]["port"]

                    address_list_copy.remove(Address(ip,port))
                    nodes_data.append(result)
                except Exception as e:
                    print(f"Error occurred: {e}")

            for address in address_list_copy:
                nodes_data.append({
                    "address": address,
                    "status": "down"
                     })
    except Exception as e:
        print(f"Error occurred: {e}")   

    return


# @app.route('/data')
# def get_data():
#     global data
#     return jsonify({'data': nodes_data})

# def update_data():
#     global data
#     # while run_event.is_set():
#     while True:
#         time.sleep(1)
#         asyncio.run(getData())

@app.route('/')
def show_data():
    global nodes_data
    asyncio.run(getData())
    # while True:
    return render_template('index.html', data=nodes_data)

if __name__ == '__main__':  


    app.run(debug=True)

