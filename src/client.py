import xmlrpc.client  
from lib.struct.address import Address

import sys
import json

server = None

def send_to_server(request):
    req = json.dumps(request)
    response = {
        "status": "redirected",
    }

    global server
    response = (server.execute(req))
    while response["status"] == "redirected":
        print(response)
        server = xmlrpc.client.ServerProxy(f'http://{response["address"]["ip"]}:{response["address"]["port"]}')
        response = (server.execute(req))
        
    print(response)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("client.py <ip> <port>")
        exit()

    server_addr = Address(sys.argv[1], int(sys.argv[2]))
    server = xmlrpc.client.ServerProxy(f'http://{server_addr.ip}:{server_addr.port}')
    
    while(True):
        command = input("Command:")

        words = command.split()

        if(words[0].lower() == "exit"):
            break

        if(words[0].lower() == "ping"):
            print(server.ping())
            continue

        if(words[0].lower() == "log"):
            print(server.request_log())
            continue

        # Check if the first word is "queue" and if there is a next word
        if len(words) > 1 and words[0].lower() == "queue":
            message = words[1]

            request = {
                "action": "queue",
                "message": message
            }
            send_to_server(request)
            
        if(words[0].lower() == "dequeue"):
            request = {
                "action": "dequeue"
            }
            send_to_server(request)
        