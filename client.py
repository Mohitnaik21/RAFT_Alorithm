import socket
import json
import random
import time
import os
class SimpleRPCClient:
    def __init__(self, total_nodes):
        self.total_nodes = total_nodes
        self.connected_nodes = 0
        self.current_node_index = 0
        self.servers = [(f'localhost', 8000 + i) for i in range(1, total_nodes + 1)]
        self.leader_server = None
      
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
            
               # Receive and print the response
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Received response: {response}")

            # Check if the response contains an election timeout message
            if "election timeout message" in response.lower():
                print(response)
            
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
        print("3. Heart Beat")
        print("4. Print the Log")
        print("5. Exit")
        

        choice = input("Enter your choice: ")

        if choice == "1":
            leader_elected = False
            while not leader_elected:
                # Randomly choose an active machine to start the election
                active_servers = [server for server in client.servers if client.send_request(server, '{"type": "check_connection"}')]
                if not active_servers:
                    print("No active machines. Election cannot be started.")
                    break

                chosen_server = random.choice(active_servers)
                print(f"\nStarting election on machine running on port {chosen_server[1]}...")
                request_data = {"type": "start_election"}
                request = json.dumps(request_data)
                response = client.send_request(chosen_server, request)
                if response and "leader" in response.lower():
                    print(response)
                    client.leader_server = chosen_server
                    print(f"The chosen server is {chosen_server}")
                    leader_elected = True
                else:
                    print("Election failed. Trying again...")
                    
        elif choice == "2":
            if not leader_elected:
                print("No leader elected yet. Please start an election first.")
            else:
                # Get the server address of the current leader
                leader_server = client.leader_server

                # Send the proposed value to the leader
                value = input("Enter the value to propose: ")
                request_data = {"type": "propose_value", "value": value}
                request = json.dumps(request_data)
                response = client.send_request(leader_server, request)

                if response:
                    print(response)
                        
        elif choice == "3":
        # Get the server address of the current leader
                leader_server = client.leader_server
                # Send a heartbeat message to the leader
                heartbeat_request = {"type": "heartbeat"}
                heartbeat_request_json = json.dumps(heartbeat_request)
                heartbeat_response = client.send_request(leader_server, heartbeat_request_json)

                # Check if the leader responded to the heartbeat
                if heartbeat_response and "alive" in heartbeat_response.lower():
                    print(f"\nLeader is alive on port {leader_server[1]}")
                else:
                    print(f"\nLeader is not alive on port {leader_server[1]}")
                    
        elif choice == "4":
            # Print the log file on the console
            print("\nLog File:")
            with open("RaftLog.txt", "r") as file:
                print(file.read())
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please try again.")

    print("Exiting the code for RAFT consensus Implementation.")
