import xmlrpc.server

class PingServer:
    def ping(self):
        return "pong"

print("Starting server on port 8000")
with xmlrpc.server.SimpleXMLRPCServer(('localhost', 8000)) as server:
    server.register_instance(PingServer())
    server.serve_forever()