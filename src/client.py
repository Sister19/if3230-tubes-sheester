import xmlrpc.client  

def main():
    print("start")
    server = xmlrpc.client.ServerProxy('http://localhost:12001')
    print("start")

    # Send a message to the server
    message = "Hello, server!"
    response = server.handle_message(message)
    print("start")
    print(response)
    return

if __name__ == "__main__":
    main()