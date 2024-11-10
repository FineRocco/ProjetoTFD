# streamletnetwork.py

import os
import random
import socket
import sys
import threading
import time
from block import Block
from message import Message, MessageType
from transaction import Transaction
import subprocess

class StreamletNetwork:
    """
    Manages a network of nodes implementing the Streamlet Protocol, coordinating epoch cycles, 
    transaction generation, and message passing among nodes in the network.
    """
    
    def __init__(self, num_nodes, delta, base_port):
        self.num_nodes = num_nodes
        self.leader = 0  # Initially, node 0 is the leader
        self.leader_port = 0
        self.global_tx_id = 0  # Global transaction counter
        self.tx_id_lock = threading.Lock()  # Lock to synchronize transaction ID generation
        self.delta = delta  # Set ∆, the network delay parameter
        self.epoch_duration = 2 * delta  # Epoch lasts for 2∆ rounds
        self.processes = []  # To store Popen process references
        self.ports = [base_port + i for i in range(num_nodes)]  # Port assignment for nodes
        print("Port allocation:", self.ports)
        
        # Initialize genesis block
        self.genesis_block = Block(epoch=0, previous_hash=b'0' * 20, transactions={})
    
    def start_network(self):
        """
        Launches each node as a separate process and waits for them to be ready.
        """
        ready_port = 6000  # Port for readiness signaling
        ready_count = 0

        # Start each node process in a new terminal
        for i in range(self.num_nodes):
            node_port = self.ports[i]
            port_list = ",".join(map(str, self.ports))  # Ports to pass to each node
            if sys.platform == "win32":
                process = subprocess.Popen(
                    ["python3", "node_script.py", str(i), str(self.num_nodes), str(node_port), port_list],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            elif sys.platform == "darwin":  # macOS
                # Using osascript to open a new terminal window
                command = f'osascript -e \'tell application "Terminal" to do script "python3 {os.path.join(os.getcwd(), "node_script.py")} {i} {self.num_nodes} {node_port} {port_list}"\''
                process = subprocess.Popen(command, shell=True)
            else:
                process = subprocess.Popen(
                    ["python3", "node_script.py", str(i), str(self.num_nodes), str(node_port), port_list]
                )
            self.processes.append(process)

        # Listen for readiness signals from nodes
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ready_socket:
            ready_socket.bind(('localhost', ready_port))
            ready_socket.listen(self.num_nodes)
            print("Waiting for nodes to be ready...")

            while ready_count < self.num_nodes:
                conn, _ = ready_socket.accept()
                with conn:
                    data = conn.recv(1024)
                    if data == b"READY":
                        ready_count += 1
                        print(f"Node {ready_count} is ready")

        print("All nodes are ready!")

    def stop_network(self):
        """
        Terminates all node processes.
        """
        
        # Terminate each node process and wait for completion
        for process in self.processes:
            process.terminate()
            process.wait()
        print("All nodes stopped.")

    def next_leader(self):
        """
        Updates the leader node for the next epoch based on round-robin rotation.
        """
        self.leader = (self.leader + 1) % self.num_nodes
        print(f"New leader: Node {self.leader}")

    def start_epoch(self, epoch):
        """
        Begins a new epoch in the network, where the designated leader node proposes a block.

        :param epoch: int - The current epoch number.
        """
        self.generate_transactions_for_epoch(epoch)
        self.next_leader()
        self.leader_port = self.ports[self.leader]
        print(f"Epoch {epoch}: Initiating block proposal by leader node {self.leader}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            start_proposal_message = Message.create_start_proposal_message(epoch, self.leader)
            try:
                sock.connect(('localhost', self.leader_port))
                sock.sendall(start_proposal_message.serialize())
                print(f"Sent START_PROPOSAL for epoch {epoch} to leader Node {self.leader}")
            except ConnectionRefusedError:
                print(f"Could not connect to leader Node {self.leader} at port {self.leader_port}")

    def run(self, total_epochs):
        """
        Executes the Streamlet consensus protocol for the specified number of epochs.

        :param total_epochs: int - The total number of epochs to be run.
        """
        for epoch in range(1, total_epochs + 1):
            print(f"=== Epoch {epoch} ===")
            self.start_epoch(epoch)
            time.sleep(self.epoch_duration)

        # After all epochs, send a display command to each node to show their blockchain state
        for port in self.ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(('localhost', port))
                    display_message = Message.create_display_blockchain_message(sender=0)
                    sock.sendall(display_message.serialize())
                    print(f"Sent DISPLAY_BLOCKCHAIN to Node at port {port}")
            except ConnectionRefusedError:
                print(f"Could not connect to Node at port {port} to display blockchain.")

    def get_next_tx_id(self):
        """
        Generates a globally unique transaction ID.

        :return: int - The next available transaction ID.
        """
        with self.tx_id_lock:
            self.global_tx_id += 1
            return self.global_tx_id

    def generate_random_transaction_for_epoch(self, epoch):
        """
        Creates a random transaction and sends it to a randomly selected node in the network for a specific epoch.

        :param epoch: int - The epoch to which the transaction belongs.
        """
        sender = f"Client{random.randint(1, 100)}"
        receiver = f"Client{random.randint(1, 100)}"
        amount = random.randint(1, 1000)

        # Generate a unique transaction ID
        tx_id = self.get_next_tx_id()
        transaction = Transaction(tx_id, sender, receiver, amount)

        # Send transaction to a random node
        target_port = random.choice(self.ports)
        transaction_message = Message.create_transaction_message(transaction, epoch, sender=0)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', target_port))
                s.sendall(transaction_message.serialize())
            print(f"Sent transaction {tx_id} from {sender} to {receiver} for {amount} coins to Node at port {target_port}.")
        except ConnectionRefusedError:
            print(f"Failed to send transaction to Node at port {target_port}.")

    def generate_transactions_for_epoch(self, epoch):
        """
        Generates a random number of transactions for a specific epoch.

        :param epoch: int - The epoch for which transactions are to be generated.
        """
        num_transactions = random.randint(1, 3)  # Random number of transactions per epoch
        for _ in range(num_transactions):
            self.generate_random_transaction_for_epoch(epoch)
