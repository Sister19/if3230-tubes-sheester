from lib.struct.address       import Address
from lib.raft          import RaftNode
from lib.app import Application
from xmlrpc.server import SimpleXMLRPCServer
# from app           import MessageQueue
import sys

def start_serving(addr: Address, contact_node_addr: Address):
    print(f"Starting Raft Server at {addr.ip}:{addr.port}")
    with SimpleXMLRPCServer((addr.ip, addr.port)) as server:
        server.register_introspection_functions()
        # server.register_instance(RaftNode(MessageQueue(), addr, contact_node_addr))
        
        app = Application()

        node = RaftNode(app, addr, contact_node_addr)
        server.register_instance(node)
        
        try:
            server.serve_forever()
        except (KeyboardInterrupt):
            node.stopThread()
            exit()



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("server.py <ip> <port> <opt: contact ip> <opt: contact port>")
        exit()

    contact_addr = None
    if len(sys.argv) == 5:
        contact_addr = Address(sys.argv[3], int(sys.argv[4]))
    server_addr = Address(sys.argv[1], int(sys.argv[2]))

    start_serving(server_addr, contact_addr)

