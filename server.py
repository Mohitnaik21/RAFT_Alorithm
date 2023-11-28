import socket
import threading
import json
import time
import random
import os

class RaftNode:
    def __init__(self, node_id, port, total_nodes):
        self.node_id = node_id
        self.port = port
        self.total_nodes = total_nodes
        self.term = 0
        self.leader_id = None
        self.votes_received = 0
        self.election_timeout = random.randint(150, 300)  # Random timeout for demonstration
        self.heartbeat_interval = 50  # Set a reasonable heartbeat interval
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', port))
        self.server_socket.listen(5)
        self.client_sockets = []
        self.servers = [(f'localhost', 8000 + i) for i in range(1, total_nodes + 1)]
        self.last_heartbeat_received = time.time()
        self.last_heartbeat_sent = time.time()
        self.last_heartbeat_received_from_leader = None
        self.log = []
        if os.path.exists("RaftLog.txt"):
            self.log_file_mode = 'a'  # Append mode
        else:
            self.log_file_mode = 'w'  # Write mode for a new file


    def start(self):
        print(f"Node {self.node_id} started on port {self.port}")
        threading.Thread(target=self.accept_connections).start()
        threading.Thread(target=self.start_heartbeat).start()
        threading.Thread(target=self.check_election_timeout).start()
        threading.Thread(target=self.check_heartbeat_interval).start()

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
                elif request_data["type"] == "heartbeat":
                    print(f"Node {self.node_id} handling heartbeat request")
                    self.handle_heartbeat(client_socket)
                elif request_data["type"] == "election_timeout_message":
                     message = request_data.get("message", "Unknown message")
                     print(f"Node {self.node_id} received election timeout message: {message}")
                     client_socket.send(f"Election timeout message: {message}".encode('utf-8'))
                elif request_data["type"] == "check_connection":
                    self.handle_check_connection(client_socket)
                elif request_data["type"] == "heartbeat_check":
                    print(f"Node {self.node_id} handling heartbeat_check request")
                    client_socket.send("Active".encode('utf-8'))
                elif request_data["type"] == "replicate_log":
                    print(f"Node {self.node_id} handling replicate_log request")
                    self.handle_replicate_log(request_data, client_socket)


            except json.JSONDecodeError:
                print(f"Node {self.node_id} received invalid JSON format: {data}")

            time.sleep(1)  # Simulate processing time

    def handle_heartbeat(self, client_socket):
         # Update the last time a heartbeat was received
            self.last_heartbeat_received = time.time()
            self.last_heartbeat_sent = time.time()
            time_to_next_heartbeat = self.calculate_time_to_next_heartbeat()
            response = {"type": "heartbeat_response", "status": "alive", "time_to_next_heartbeat": time_to_next_heartbeat}
            client_socket.send(json.dumps(response).encode('utf-8'))
            print(f"Node {self.node_id} sent heartbeat response. Next heartbeat in: {time_to_next_heartbeat} seconds")
            
            self.election_timeout = random.randint(150, 300)
            print(f"Received heartbeat. Resetting election timeout.")
            
    def handle_check_connection(self, client_socket):
        inactive_machines = []

        for server_address in self.servers:
            print(f"Checking connection to machine at {server_address}")
            response = self.send_request(server_address, '{"type": "heartbeat_check"}')

            if response and "Active" in response:
                print(f"Machine at {server_address} is active")
            else:
                port_number = server_address[1]
                inactive_machines.append(port_number)
                print(f"Failed to check connection to machine at {server_address}")

        if not inactive_machines:
            print("Sending message: All the machines are active")
            client_socket.send("All the machines are active".encode('utf-8'))
        else:
            # Notify about inactive machines
            message = ", ".join([f"The machine on port {port_number} is not active" for port_number in inactive_machines])
            print(f"Sending message: {message}")
            client_socket.send(message.encode('utf-8'))

        
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
                if (
                     response_data.get("type") == "VOTE_GRANTED"
                    and int(response_data.get("term", 0)) == self.term
                    ):
                    self.votes_received += 1
                print(f"Current term in Node {self.node_id}: {self.term}")
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

            # Create a log entry with the correct index
            index = len(self.log) + 1
            log_entry = {
                "Machine ID": f"Machine {self.node_id}",
                "Index": index,
                "Term": self.term,
                "Value": value,
                "Leader Id": self.leader_id
            }

            # Append the log entry to the leader's log
            self.append_log_entry(log_entry)

            # Replicate the log entry to other nodes
            self.replicate_log_entry(log_entry)

            # For demonstration purposes, simulate value acceptance
            client_socket.send(f'Node {self.node_id} proposed value {value} accepted'.encode('utf-8'))
        else:
            print(f"Node {self.node_id} is not the leader. Cannot propose value.")

    
    def append_log_entry(self, log_entry):
        # Append the log entry to the leader's log
        # In a real implementation, you would store the log persistently
        # and handle log compaction, snapshotting, etc.
        print(f"Node {self.node_id} appending log entry: {log_entry}")
        self.log.append(log_entry)
        print(f"Log entry {log_entry}")
         # Write the log entry to the log file
        with open("RaftLog.txt", self.log_file_mode) as log_file:
            log_file.write(
                f"{log_entry['Machine ID']} | {log_entry['Index']} | {log_entry['Term']} | {log_entry['Value']} | {log_entry['Leader Id']}\n"
            )


    def replicate_log_entry(self, log_entry):
        if self.leader_id == self.node_id:
            # Send AppendEntries RPCs to all followers to replicate the new log entry
            for node_id in range(1, self.total_nodes + 1):
                if node_id != self.node_id:
                    # Create a log entry for each machine with the correct machine ID
                    replicated_log_entry = {
                        "Machine ID": f"Machine {node_id}",
                        "Index": log_entry["Index"],
                        "Term": log_entry["Term"],
                        "Value": log_entry["Value"],
                        "Leader Id": log_entry["Leader Id"]
                    }

                    # Send the replicated log entry to the follower
                    request_data = {"type": "replicate_log", "log_entry": replicated_log_entry}
                    request = json.dumps(request_data)
                    response = self.send_request((f'localhost', 8000 + node_id), request)
                    print(f"Response received from replicate_log: {response}")


    def handle_replicate_log(self, request_data, client_socket):
        received_log_entry = request_data.get("log_entry")
        if received_log_entry:
            # Check if the log entry is valid and can be appended to the follower's log
            if self.validate_append_entries(request_data):
                # Append the log entry to the follower's log
                self.append_log_entry(received_log_entry)
                # Respond to the leader indicating successful replication
                response = {"type": "log_replication_success"}
                client_socket.send(json.dumps(response).encode('utf-8'))
                print(f"Node {self.node_id} successfully replicated log entry: {received_log_entry}")
            else:
                # Respond to the leader indicating failure to replicate
                response = {"type": "log_replication_failure"}
                client_socket.send(json.dumps(response).encode('utf-8'))
                print(f"Node {self.node_id} failed to replicate log entry: {received_log_entry}")

    def validate_append_entries(self, request_data):
        # Validate if the AppendEntries RPC can be processed by the follower
        received_log_entry = request_data.get("log_entry")
        prev_log_index = received_log_entry.get("Index", 0) - 1
        prev_log_term = received_log_entry.get("Term", 0)

        if prev_log_index >= 0 and prev_log_index < len(self.log):
            # Check if the follower's log contains an entry at the previous log index and term
            existing_entry = self.log[prev_log_index]
            if existing_entry["Term"] == prev_log_term:
                # The entries match, so the follower can append the new entry
                return True
            else:
                # The follower's log entry at the previous log index has a different term
                print(f"Node {self.node_id} rejected log entry due to term mismatch: {received_log_entry}")
                return False
        elif prev_log_index == len(self.log):
            # The follower doesn't have an entry at the previous log index, but it's valid to append
            return True
        else:
            # The leader's log is inconsistent with the follower's log
            print(f"Node {self.node_id} rejected log entry due to inconsistent logs: {received_log_entry}")
            return False



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
        
    def start_heartbeat(self):
        while True:
            time.sleep(self.heartbeat_interval)
            if self.leader_id == self.node_id:
                # Send heartbeat messages to followers
                self.last_heartbeat_sent = time.time()
                for node_id in range(1, self.total_nodes + 1):
                    if node_id != self.node_id:
                        request_data = {"type": "heartbeat", "term": self.term}
                        request = json.dumps(request_data)
                        self.send_request((f'localhost', 8000 + node_id), request)
                        print(f"Node {self.node_id} sent heartbeat to Node {node_id}")

    def check_heartbeat_interval(self):
        while True:
            time.sleep(1)
            if self.leader_id == self.node_id:
                time_to_next_heartbeat = self.calculate_time_to_next_heartbeat()
                print(
                    f"Heartbeat sent to followers. Next heartbeat in: {time_to_next_heartbeat} seconds"
                )
            else:
                elapsed_time_since_heartbeat = (
                    time.time() - self.last_heartbeat_received
                )
                # if self.leader_id != self.node_id:
                #     print(
                #     f"Node {self.node_id} election timeout: {self.election_timeout} seconds"
                # )

                # Reset election timeout if heartbeat received
                if elapsed_time_since_heartbeat < self.heartbeat_interval / 1000:
                    self.election_timeout = random.randint(150, 300)
                    print(f"Received heartbeat. Resetting election timeout.")
                    time_to_next_heartbeat = self.calculate_time_to_next_heartbeat()
    
    def calculate_time_to_next_heartbeat(self):
        current_time = time.time()
        elapsed_time_since_heartbeat = current_time - self.last_heartbeat_sent  
        time_to_next_heartbeat = max(0, self.heartbeat_interval - elapsed_time_since_heartbeat)
        return time_to_next_heartbeat
                
    def check_election_timeout(self):
        while True:
            time.sleep(1)
            current_time = time.time()
              # Calculate the time elapsed since the last heartbeat
            elapsed_time_since_heartbeat = current_time - self.last_heartbeat_received
            self.election_timeout -= 1
            if self.leader_id != self.node_id:
                 print(f"Node {self.node_id} election timeout: {self.election_timeout} seconds")
            if self.election_timeout == 0 and elapsed_time_since_heartbeat > self.heartbeat_interval / 1000:
                 print(f"No heartbeat message received from the leader {self.leader_id} on port {self.port}")
                 message = f"The election time clock for all the followers has timed out."
                 print(message)
                # Send the message to the client
                 if self.leader_id is not None:
                    # Assuming there is a leader, send the message to the client of the leader
                    leader_server = (f'localhost', 8000 + self.leader_id)
                    request_data = {"type": "election_timeout_message", "message": message}
                    request = json.dumps(request_data)
                    self.send_request(leader_server, request)
                # Start a new election
                    print(f"Start a new election to elect a new leader.")

if __name__ == '__main__':
    total_nodes = int(input("Enter the number of machines in the cluster: "))
    node_id = int(input("Enter the node ID: "))
    port = 8000 + node_id
    
    # Create or clear the log file when the program starts
    with open("RaftLog.txt", "w") as log_file:
        log_file.write("Machine ID       |   Index | Term | Value | Leader Id\n")
        log_file.write("------------------------------------------------------\n")

    raft_node = RaftNode(node_id, port, total_nodes)
    threading.Thread(target=raft_node.start).start()

    while True:
        pass
