import socket
import json
import random
class SimpleRPCClient:
    def __init__(self, total_nodes):
        self.total_nodes = total_nodes
        self.connected_nodes = 0
        self.current_node_index = 0
        self.servers = [(f'localhost', 8000 + i) for i in range(1, total_nodes + 1)]

    def send_request(self, server_address, request):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Connecting to machine at {server_address}")
            client_socket.connect(server_address)
            port = server_address[1]
            print(f"Connected to machine running on port {port}")
            self.connected_nodes += 1
            client_socket.send(request.encode('utf-8'))
            print(f"Sent request: {request}")
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Received response: {response}")
            client_socket.close()
            return response
        except ConnectionRefusedError:
            print(f"Connection to {server_address} refused.")
            client_socket.close()
            return None

if __name__ == "__main__":
    total_nodes = int(input("Enter the number of machines in the cluster: "))
    client = SimpleRPCClient(total_nodes)

    print(f"\nNumber of machines in the cluster: {client.total_nodes}")
    print("Connected machines:")
    for server_address in client.servers:
        print(f"- Machine running on port {server_address[1]}")

    while True:
        print("\nOptions:")
        print("1. Start Election")
        print("2. Propose Value")
        print("3. Next Machine")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            leader_elected = False
            while not leader_elected:
                # Randomly choose a machine to start the election
                chosen_server = random.choice(client.servers)
                print(f"\nStarting election on machine running on port {chosen_server[1]}...")
                request_data = {"type": "start_election"}
                request = json.dumps(request_data)
                response = client.send_request(chosen_server, request)
                if response and "leader" in response.lower():
                    print(response)
                    leader_elected = True
                else:
                    print("Election failed. Trying again...")
                    
        elif choice == "2":
            value = input("Enter the value to propose: ")
            request_data = {"type": "propose_value", "value": value}
            request = json.dumps(request_data)
            response = client.send_request(client.servers[client.current_node_index], request)
            if response:
                print(response)
        elif choice == "3":
            client.current_node_index = (client.current_node_index + 1) % client.total_nodes
            print(f"\nSwitching to machine running on port {client.servers[client.current_node_index][1]}")
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")

    if client.connected_nodes == client.total_nodes:
        print(f"\nConnected to all {client.total_nodes} machines.")
    else:
        print(f"\nOnly connected to {client.connected_nodes} out of {client.total_nodes} machines.")
