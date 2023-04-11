from lib.struct.address       import Address
from typing        import Any, List
from enum          import Enum

import json
import time
import xmlrpc.client 
import xmlrpc.server 
import asyncio
import threading 

class RaftNode():
    HEARTBEAT_INTERVAL   = 1
    ELECTION_TIMEOUT_MIN = 2
    ELECTION_TIMEOUT_MAX = 3 
    RPC_TIMEOUT          = 0.5 

    class NodeType(Enum):
        LEADER    = 1
        CANDIDATE = 2
        FOLLOWER  = 3

    def __init__(self, application: Any, addr: Address, contact_addr: Address = None):
        # socket.setdefaulttimeout(RaftNode.RPC_TIMEOUT)
        self.address:             Address           = addr
        self.type:                RaftNode.NodeType = RaftNode.NodeType.FOLLOWER
        self.log:                 List[str, str]    = []
        self.app:                 Any               = application
        self.election_term:       int               = 0
        self.cluster_addr_list:   List[Address]     = []
        self.cluster_leader_addr: Address           = None
        
        self.server_listener   : xmlrpc.server.SimpleXMLRPCServer = xmlrpc.server.SimpleXMLRPCServer((addr.ip, int(addr.port)))       
        
        if contact_addr is None:
            self.cluster_addr_list.append(self.address)
            self.__initialize_as_leader()
        else:
            self.__try_to_apply_membership(contact_addr)
            
    
    def __print_log(self, text: str):
        print(f"[{self.address}] [{time.strftime('%H:%M:%S')}] {text}")
        
    def __initialize_as_leader(self):
        self.__print_log("Initialize as leader node...")
        self.cluster_leader_addr = self.address
        self.type                = RaftNode.NodeType.LEADER
        request = {
            "cluster_leader_addr": self.address
        }
        
        for address in self.cluster_addr_list:
            # TODO : Send request to all node
            pass
        
        # TODO : Inform to all node this is new leader
        self.run_event = threading.Event()
        self.run_event.set()
        self.heartbeat_thread = threading.Thread(target=asyncio.run,args=[self.__leader_heartbeat(run_event=self.run_event)])
        self.heartbeat_thread.start()
        
    def stopThread(self):
        if(hasattr(self,"run_event")):
            self.run_event.clear()
            self.heartbeat_thread.join()
        
    async def __leader_heartbeat(self,run_event):
        while run_event.is_set():
            try:
                self.__print_log("[Leader] Sending heartbeat...")
                tasks=[]
                for address in self.cluster_addr_list:
                    if address != self.address:
                        task = asyncio.create_task(self.__send_heartbeat(address))
                        tasks.append(task)
                
                # await asyncio.gather(*tasks)
                if(tasks):
                    done, _ = await asyncio.wait(tasks, timeout=1.0, return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        try:
                            result = await task
                            if(result == False):
                                self.__print_log(f"No response from {address}: {result}")
                            # self.__print_log(f"Heartbeat response from {address}: {result}")
                        except Exception as e:
                            print(f"Error occurred during heartbeat for {address}: {e}")
            
                
            except Exception as e:
                print(f"Error occurred during heartbeat: {e}")
        
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)
    
    def __try_to_apply_membership(self,contact_addr):
        self.__print_log("Try to apply membership...")
        redirected_addr = contact_addr
        response = {
            "status": "redirected",
            "address": {
                "ip":   contact_addr.ip,
                "port": contact_addr.port,
            }
        }
        while response["status"] != "success":
            #TODO: send to contact_addr and get response
            #response = send and receive response
            redirected_addr = Address(response["address"]["ip"], response["address"]["port"])
            
            # break
            response        =  self.__send_request(self.address, "apply_membership", redirected_addr)
        self.log                 = response["log"]
        self.cluster_addr_list   = response["cluster_addr_list"]
        self.cluster_leader_addr = redirected_addr
        self.__print_log("Succesfully applied membership to cluster with leader at " + str(self.cluster_leader_addr))
        return
    
        #BLOCKING
    def __send_request(self, request: Any, rpc_name: str, addr: Address) -> "json":
        # try:
        node         = xmlrpc.client.ServerProxy(f"http://{addr.ip}:{addr.port}")
        json_request = json.dumps(request)
        rpc_function = getattr(node, rpc_name)
        response     = json.loads(rpc_function(json_request))
        self.__print_log(response)
        return response
        # except Exception as e:
        #     print(f"Error sending message to {addr.ip}:{addr.port}: {e}")
        #     return "EXCEPTION"
        
    async def __send_heartbeat(self, addr):
        try:
            client = xmlrpc.client.ServerProxy(f"http://{addr.ip}:{addr.port}")
            result = client.heartbeat(json.dumps(self.address))
            return True
        except:
            return False
        # return json.loads(result)
        
    def apply_membership(self,request):
        if(self.type != RaftNode.NodeType.LEADER):      #TODO: CURRENTLY DOESNT HANDLE IF CANDIDATE
            response = {
            "status": "redirected",
            "address": self.cluster_leader_addr
            }
        else:
            req = json.loads(request)
            ip = req["ip"]
            port = req["port"]
            self.__print_log(f"Received apply_membership request from {ip}:{port}")
            self.cluster_addr_list.append(Address(ip, port))
            response = {
                "status": "success",
                "log": self.log,
                "cluster_addr_list": self.cluster_addr_list
            }
            
        return json.dumps(response)
    
    def heartbeat(self,request):
        req = json.loads(request)
        ip = req["ip"]
        port = req["port"]
        self.__print_log(f"Received heartbeat from {ip}:{port}")
        return "success"
    
    async def send_message(self,address,message):
        try:
            print("makeclient")
            ip=address.ip
            port = address.port
            client = xmlrpc.client.ServerProxy(f"http://{ip}:{port}")
            print(f"send mesasage")
            result = client.handle_message(message)
            print(f"finish")
            # result = await asyncio.to_thread(server.handle_message, message) #??????????
            print(result)
        except Exception as e:
            print(f"Error sending message to {ip}:{port}: {e}")
            
            

        
    
    def handle_message(self,message):
        return "Hello" + message
    
async def main():
    print("start")
    node1 = RaftNode(None, Address("localhost","12001"))
    node2 = RaftNode(None, Address("localhost","12002"),Address("localhost","12001"))
    node3 = RaftNode(None, Address("localhost","12003"),Address("localhost","12001"))
    
    await node1.send_message("Hello","localhost","12002")
    # await node1.send_message("Hello","localhost","12003")

if __name__ == "__main__":
    asyncio.run(main())