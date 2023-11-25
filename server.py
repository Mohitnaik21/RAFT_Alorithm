import socket
import threading
import json
import time

class RaftNode:
    def __init__(self, node_id, port, total_nodes):
        self.node_id = node_id
        self.port = port
        self.total_nodes = total_nodes
        self.term = 0
        self.leader_id = None
        self.votes_received = 0

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', port))
        self.server_socket.listen(5)

        self.client_sockets = []

    def start(self):
        print(f"Node {self.node_id} started on port {self.port}")
        self.accept_connections()

    def accept_connections(self):
        print(f"Node {self.node_id} is now accepting connections...")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Accepted connection from {addr}")
            self.client_sockets.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            print(f"Node {self.node_id} received request: {data}")

            try:
                request_data = json.loads(data)
                if request_data["type"] == "start_election":
                    print(f"Node {self.node_id} handling start_election request")
                    self.start_election(client_socket)
                elif request_data["type"] == "propose_value":
                    value = request_data.get("value")
                    print(f"Node {self.node_id} handling propose_value request with value {value}")
                    self.propose_value(value, client_socket)
                elif request_data["type"] == "get_leader":
                    print(f"Node {self.node_id} handling get_leader request")
                    self.get_leader(client_socket)
                elif request_data["type"] == "request_vote":
                    print(f"Node {self.node_id} handling request_vote request")
                    self.handle_request_vote(request_data, client_socket)
            except json.JSONDecodeError:
                print(f"Node {self.node_id} received invalid JSON format: {data}")

            time.sleep(1)  # Simulate processing time

    def handle_request_vote(self, request_data, client_socket):
        received_term = request_data.get("term", 0)
        if received_term > self.term:
            self.term = received_term
            # Vote for the requesting node
            response = {"type": "VOTE_GRANTED", "term": self.term}
            client_socket.send(json.dumps(response).encode('utf-8'))
            print(response)
            # print(f"Node {self.node_id} voted for Node {request_data['node_id']} in term {self.term}")
        else:
            # Do not vote for the requesting node
            response = {"type": "VOTE_DENIED", "term": self.term}
            client_socket.send(json.dumps(response).encode('utf-8'))
            print(f"Node {self.node_id} denied vote for Node {request_data['node_id']} in term {self.term}")
        
        print(f"Response from handle_request_vote: {response}")
# ... (unchanged code)

    def start_election(self, client_socket):
        self.term += 1
        print(f"Node {self.node_id} started an election in term {self.term}")
        # Send vote requests to other nodes
        for node_id in range(1, self.total_nodes + 1):
            if node_id != self.node_id:
                request_data = {"type": "request_vote", "term": self.term}
                request = json.dumps(request_data)
                response = self.send_request((f'localhost', 8000 + node_id), request)
                print(f"Response recieved from handle_request_vote to start_election : {response}")
                print(response)
                if response:
                 response_data = json.loads(response)
                 print(response_data)
                 print(response_data.get("type"))
                 print(response_data.get("term"))
                 print(self.term)
                if (
                     response_data.get("type") == "VOTE_GRANTED"
                    and int(response_data.get("term", 0)) == self.term
                    ):
                    self.votes_received += 1
                print(f"Current term in Node {self.node_id}: {self.term}")
                print(self.votes_received)
                print(self.total_nodes // 2)
        # Simulate a majority of votes received, become leader
        if self.votes_received > self.total_nodes // 2:
            self.leader_id = self.node_id
            print(f"Node {self.node_id} elected as the leader in term {self.term}")
            client_socket.send(f'Node {self.node_id} elected as the leader in term {self.term}'.encode('utf-8'))
        else:
            print(f"Election failed for node {self.node_id} in term {self.term}")

    def propose_value(self, value, client_socket):
        if self.leader_id == self.node_id:
            # Implement Raft consensus logic for proposing a value
            print(f"Node {self.node_id} proposing value {value} in term {self.term}")

            # For demonstration purposes, simulate value acceptance
            client_socket.send(f'Node {self.node_id} proposed value {value} accepted'.encode('utf-8'))
        else:
            print(f"Node {self.node_id} is not the leader. Cannot propose value.")

    def get_leader(self, client_socket):
        client_socket.send(f'Current leader: Node {self.leader_id}'.encode('utf-8'))

    def send_request(self, server_address, request):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Node {self.node_id} connecting to {server_address}")
            client_socket.connect(server_address)
            print(f"Node {self.node_id} connected to {server_address}")
            print(f"Node {self.node_id} sending request: {request}")
            client_socket.send(request.encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            client_socket.close()
            print(f"Node {self.node_id} received response: {response}")
            return response
        except ConnectionRefusedError:
            print(f"Node {self.node_id} connection to {server_address} refused.")
            client_socket.close()
            return None

if __name__ == '__main__':
    total_nodes = int(input("Enter the number of machines in the cluster: "))
    node_id = int(input("Enter the node ID: "))
    port = 8000 + node_id

    raft_node = RaftNode(node_id, port, total_nodes)
    threading.Thread(target=raft_node.start).start()

    while True:
        pass
