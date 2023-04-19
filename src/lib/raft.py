from lib.struct.address       import Address
from typing        import Any, List
from enum          import Enum

import math
import json
import time
import xmlrpc.client 
import aioxmlrpc.client 
import aiohttp_xmlrpc.client
import xmlrpc.server 
import asyncio
import threading 
import random

class RaftNode():
    HEARTBEAT_INTERVAL   = 1 #this interval hasnt been added with transmission time
    ELECTION_TIMEOUT_MIN = 5
    ELECTION_TIMEOUT_MAX = 10
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
        
        if contact_addr is None:
            self.cluster_addr_list.append(self.address)
            asyncio.run(self.__initialize_as_leader())
        else:
            self.__try_to_apply_membership(contact_addr)
            
    def __print_log(self, text: str):
        print(f"[{self.address}] [{time.strftime('%H:%M:%S')}] {text}")
        
    async def __initialize_as_leader(self):
        self.__print_log("Try to Initialize as leader node...")
        self.cluster_leader_addr = self.address

        self.type                = RaftNode.NodeType.CANDIDATE

        self.election_term +=1

        request = {
            "cluster_leader_addr":
            {
                "ip": self.cluster_leader_addr.ip,
                "port": self.cluster_leader_addr.port
            },

            "election_term": self.election_term
        }
        
        if(len(self.cluster_addr_list) != 1 ): #check if there is only one node in cluster, if so, skip election
            #Vote for self
            approval_num = 1 #self approval 

            #Send vote request to all nodes
            try:
                self.__print_log("Requesting Votes...")
                tasks=[]
                for address in self.cluster_addr_list:
                    if address != self.address:
                        task = asyncio.create_task(self.__send_aio_request(request, "request_vote", address))
                        tasks.append(task)
                
                # await asyncio.gather(*tasks)
                if(tasks):
                    done, _ = await asyncio.wait(tasks,timeout = 5)
                    for task in done:
                        try:
                            result = await task
                            if(result["status"] == "ack"):
                                approval_num+=1
                                self.__print_log(f"Gained approval from {address}: {result}")
                            # self.__print_log(f"Heartbeat response from {address}: {result}")
                        except Exception as e:
                            print(f"Error occurred for {address}")
        
            
            except Exception as e:
                print(f"Error occurred during requesting vote: {e}")   
            
            if (approval_num <= math.floor(len(self.cluster_addr_list)/2)):
                return #Election fail: wait next term
            
        
        #Election success
        self.type                = RaftNode.NodeType.LEADER
        self.__cancel_timeout()
        self.__print_log("Succesfully initialized as leader node")
        self.run_event = threading.Event()
        self.run_event.set() 
        self.heartbeat_thread = threading.Thread(target=asyncio.run,args=[self.__leader_heartbeat(run_event=self.run_event)])
        self.heartbeat_thread.start() 
        
        
        
    
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
        while response["status"] != "success":  #send response to leader
            redirected_addr = Address(response["address"]["ip"], response["address"]["port"])
            response        =  self.__send_request(self.address, "apply_membership", redirected_addr)
        
        self.cluster_leader_addr    = redirected_addr
        self.log                    = response["log"]
        self.election_term          = response["election_term"]
        self.cluster_addr_list      = self.address_dict_to_list(response["cluster_addr_list"])#turn json dicts back into address
        
        self.__print_log("Succesfully applied membership to cluster with leader at " + str(self.cluster_leader_addr))
        
        self.__start_timeout()
        return      
    
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
            
            addr = Address(ip, port)
            
            if(self.is_address_in_list(addr,self.cluster_addr_list) == False):
                self.__print_log("Appending address to log")
                self.cluster_addr_list.append(addr)
            
            response = {
                "status": "success",
                "log": self.log,
                "election_term": self.election_term,
                "cluster_addr_list": self.cluster_addr_list
            }
            
        return json.dumps(response)
 
    def __send_request(self, request: Any, rpc_name: str, addr: Address) -> "json":
        #BLOCKING
        try:
            node         = xmlrpc.client.ServerProxy(f"http://{addr.ip}:{addr.port}")
            json_request = json.dumps(request)
            rpc_function = getattr(node, rpc_name)
            response     = json.loads(rpc_function(json_request))
            self.__print_log(response)
            return response
        except Exception as e:
            print(f"Error sending message to {addr.ip}:{addr.port}")
            return "EXCEPTION"
    
    async def __leader_heartbeat(self,run_event):                
        while run_event.is_set():
            request = {
                "log": self.log,
                "election_term": self.election_term,
                "cluster_addr_list": self.cluster_addr_list,
                "cluster_leader_addr": self.address,
            }
            
            try:
                self.__print_log("[Leader] Sending heartbeat...")
                tasks=[]
                address_list_copy = []
                for address in self.cluster_addr_list:
                    if address != self.address:
                        address_list_copy.append(address)
                        task = asyncio.create_task(self.__send_aio_request(request,"heartbeat",address))
                        tasks.append(task)
                
                # await asyncio.gather(*tasks)
                if(tasks):
                    done, _ = await asyncio.wait(tasks,timeout = 3)
                    for task in done:
                        try:
                            result = await task
                            try:
                                if(result["status"]== "success"):
                                    ip = result["address"]["ip"]
                                    port = result["address"]["port"]
                                    address_list_copy.remove(Address(ip,port))
                            except:
                                pass
                        except Exception as e:
                            print(f"Error occurred during heartbeat: {e}")
                

                for address in address_list_copy:
                    self.__print_log(f"No Response from {address}")


            except Exception as e:
                print(f"Error occurred during heartbeat: {e}")
        
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)
      
    async def __send_aio_request(self, request: Any, rpc_name: str, addr: Address):        
        #NON BLOCKING
        try:
            node = aiohttp_xmlrpc.client.ServerProxy(f"http://{addr.ip}:{addr.port}") #this library doesnt have timeouts?
            # client._transport.timeout = RaftNode.RPC_TIMEOUT

            json_request = json.dumps(request)
            rpc_function = getattr(node, rpc_name)
            response     =  json.loads(await rpc_function(json_request))
            # self.__print_log(response)
            await node.close()
            return response
        
        except Exception as e:
            await node.close()
            # print("Exception:", e)

            return "error"
        # return json.loads(result)
        
    def heartbeat(self,request):
        self.__reset_timeout()
        
        req = json.loads(request)
        
        self.log = req["log"]
        self.election_term = req["election_term"]
        
        self.cluster_addr_list = self.address_dict_to_list(req["cluster_addr_list"])   #turn json dicts back into address
        
        ip = req["cluster_leader_addr"]["ip"]
        port = req["cluster_leader_addr"]["port"]
        
        self.cluster_leader_addr = Address(ip, port)

        self.__print_log(f"Received heartbeat from {ip}:{port}")

        response = {
            "status":"success",
            "address":  {
                "ip": self.address.ip,
                "port": self.address.port
            }
            }
        return json.dumps(response)
    

    def __start_timeout(self):
        #Start election timeout timer
        random_timeout = random.uniform(RaftNode.ELECTION_TIMEOUT_MIN, RaftNode.ELECTION_TIMEOUT_MAX)
        self.timeout_timer = threading.Timer(random_timeout, self.__election) #calls election after timeout
        self.timeout_timer.start()

    def __cancel_timeout(self):
        #stops timeout timer 
        if(hasattr(self,"timeout_timer")):
            if self.timeout_timer.is_alive():
                self.timeout_timer.cancel()
            
    def __reset_timeout(self):
        #Reset election timeout timer
        self.__cancel_timeout()
        self.__start_timeout()
        
    def stopThread(self):
        #Stop Leader Heartbeat thread and election timeout timer SAFELY
        if(hasattr(self,"run_event")):
            self.run_event.clear()
            self.heartbeat_thread.join()
        self.__cancel_timeout()     

    def __election(self):
        #Start election
        self.__print_log("Election Timer Timed out.")
        self.__start_timeout()
        asyncio.run(self.__initialize_as_leader())
    
    def request_vote(self,req):
        request = json.loads(req)

        election_term = request["election_term"]

        #If node has already voted this term
        if(self.election_term >= election_term):
            response = {"status":"noack"}
        else:
            ip = request["cluster_leader_addr"]["ip"]
            port = request["cluster_leader_addr"]["port"]

            #if node hasnt voted, vote and reset timeout
            self.__print_log(f"Voted for {ip}:{port} in election term {election_term}")
            self.__reset_timeout()
            
            self.election_term = request["election_term"]
            response = {"status":"ack"}
        return json.dumps(response)
       
    def is_address_in_list(self,target_address,address_list):
        for address in address_list:
            if address == target_address:
                return True
        return False

    def address_dict_to_list(self,cluster_addr_list_dict):
        cluster_addr_list = []
        for d in cluster_addr_list_dict:   #turn json dicts back into address
            address = Address(d["ip"], d["port"])
            cluster_addr_list.append(address)
        return cluster_addr_list