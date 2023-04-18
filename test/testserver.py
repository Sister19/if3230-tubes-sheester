import xmlrpc.server

class PingServer:
    def ping(self):
        return "pong"

with xmlrpc.server.SimpleXMLRPCServer(('localhost', 8000)) as server:
    server.register_instance(PingServer())
    server.serve_forever()