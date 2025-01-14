# 🌟 RAFT Algorithm Implementation 🌟

This repository provides an implementation of the **RAFT consensus algorithm** using Python. The RAFT algorithm is a distributed consensus protocol designed to manage a replicated log, ensuring consistency across distributed systems.

---

## 🚀 Features

1. **👑 Leader Election**:
   - Nodes in the cluster elect a leader to handle requests.
   - An election can be triggered by any node when a leader is not detected.

2. **🔄 Log Replication**:
   - Ensures that all nodes maintain consistent logs by replicating changes from the leader.

3. **💓 Heartbeat Mechanism**:
   - The leader sends periodic heartbeats to followers to maintain authority and prevent unnecessary elections.

4. **📥 Catch-up Mechanism**:
   - Synchronizes logs among nodes if a node rejoins after being offline.

5. **🛡️ Fault Tolerance**:
   - Handles node failures and recovers when nodes rejoin the cluster.

---

## 🛠️ Components

### 1. **Server (Node)**
The server represents a node in the RAFT cluster. Each node:
- Listens for requests from other nodes or clients.
- Participates in elections and votes for leaders.
- Replicates logs from the leader.

### 2. **Client**
The client interacts with the RAFT cluster by:
- Triggering leader elections.
- Proposing new values to be added to the replicated log.
- Sending heartbeat messages to check the status of the leader.
- Viewing the current log state.

---

## 📖 How to Run

### Prerequisites
- Python 3.7+ 🐍
- Socket programming and threading support.

### Steps

1. **🔗 Clone the Repository**
   ```bash
   git clone https://github.com/Mohitnaik21/RAFT_Algorithm.git
   cd RAFT_Algorithm
   ```

2. **📡 Start Server Nodes**
   Repeat this step for the total number of nodes in the cluster. For example, if you have 3 machines in the cluster:
   ```bash
   python server.py
   ```
   You'll be prompted to enter details:
   ```plaintext
   Enter the number of machines in the cluster: 3
   Enter the node ID: 1
   ```
   Repeat this step for each machine, incrementing the node ID for each instance (e.g., 2, 3, etc.).

3. **💻 Start the Client**
   Launch the client to interact with the RAFT cluster:
   ```bash
   python client.py
   ```

4. **📊 Interact with the Cluster**
   The client provides the following options:
   - **1️⃣ Start Election**: Trigger a leader election among nodes.
   - **2️⃣ Propose Value**: Propose a value to be added to the replicated log.
   - **3️⃣ Heartbeat**: Check the health of the leader.
   - **4️⃣ Print the Log**: Display the current state of the log file.
   - **5️⃣ Exit**: Terminate the client session.

---

## 📂 Log File

Logs are stored in a file named `RaftLog.txt`:
- **Format**:  
  `Machine ID | Index | Term | Value | Leader Id`
- The log ensures that all nodes maintain consistent states.

---

## 🎥 Execution Video

[Click here to view the execution video on Google Drive](https://drive.google.com/file/d/1Gsk40QuL3URFt7kYtO3QWGUc30eJAg1_/view?usp=sharing) 📽️

*Make sure to watch it to understand the workflow and see RAFT in action.*

---

## 🛡️ Example Workflow

1. Start 3 server nodes on different ports (as explained above).
2. Use the client to:
   - Start an election.
   - Elect a leader.
   - Propose new values to the leader.
   - View the replicated log.
3. Simulate a node failure by stopping one server and then restarting it to observe the **catch-up mechanism**.

---

## 🤝 Contributing

Contributions to this project are welcome! To contribute:
1. 🍴 Fork the repository.
2. 🌿 Create a feature branch.
3. 📝 Commit your changes.
4. 📨 Submit a pull request.

---

## 🙌 Acknowledgments

- Inspired by the [RAFT consensus algorithm paper](https://raft.github.io/).
- Special thanks to the open-source community for their contributions to distributed systems research.

---

✨ We hope this README gives you all the details you need to get started! Happy coding! 🎉
