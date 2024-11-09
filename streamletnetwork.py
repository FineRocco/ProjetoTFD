import os
import random
import socket
import sys
import threading
import time
from message import Message, MessageType
from node import Node
from block import Block
from transaction import Transaction
import subprocess

class StreamletNetwork:
    """
    Manages a network of nodes implementing the Streamlet Protocol, coordinating epoch cycles, 
    transaction generation, and message passing among nodes in the network.
    """
    
    current_directory = os.path.dirname(os.path.abspath(__file__))
    node_script_path = os.path.join(current_directory, "node_script.py")

    def __init__(self, num_nodes, delta, base_port):
        """
        Initializes a StreamletNetwork instance with multiple nodes.

        :param num_nodes: int - The number of nodes in the network.
        :param delta: int - The network delay parameter (∆), determining epoch duration.
        :param base_port: int - The starting port number; each node is assigned an incremented port.
        """
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

        self.transaction_thread = None  # To store the transaction generation thread
        self.generate_transactions = True  # Flag to control transaction generation

        # Initialize genesis block for each node
        self.genesis_block = Block(epoch=0, previous_hash=b'0', transactions=[])
        for node in self.processes:
            node.blockchain.append(self.genesis_block)  # Start all nodes with the genesis block
            node.notarized_blocks[0] = self.genesis_block  # Genesis block is notarized from the start

    def start_network(self):
        """
        Launches each node as a separate process and waits for them to be ready. 
        Starts the transaction generation thread once nodes are ready.
        """
        ready_port = 6000  # Port for readiness signaling
        ready_count = 0
        # Start each node process in a new terminal
        for i in range(self.num_nodes):
            node_port = self.ports[i]
            port_list = ",".join(map(str, self.ports))  # Ports to pass to each node
            if sys.platform == "win32":
                process = subprocess.Popen(
                    ["python3", node_script_path, str(i), str(self.num_nodes), str(node_port), port_list],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            elif sys.platform == "darwin":  # macOS
                command = f'osascript -e \'tell application "Terminal" to do script "python3 {self.node_script_path} {i} {self.num_nodes} {node_port} {port_list}"\''
                process = subprocess.Popen(command, shell=True)
            else:
                process = subprocess.Popen(
                    ["python3", node_script_path, str(i), str(self.num_nodes), str(node_port), port_list]
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

        # Start the transaction generation thread
        self.transaction_thread = threading.Thread(target=self.generate_transactions_periodically, args=(5,))
        self.transaction_thread.daemon = True  # Daemon thread to close with main program
        self.transaction_thread.start()
        print("Transaction generation thread started.")

    def stop_network(self):
        """
        Terminates all node processes and stops the transaction generation thread.
        """
        # Stop transaction generation
        self.generate_transactions = False
        if self.transaction_thread:
            self.transaction_thread.join()  # Wait for transaction thread to finish

        # Terminate each node process and wait for completion
        for process in self.processes:
            process.terminate()
            process.wait()
        print("All nodes and transaction generation thread stopped.")

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
        self.next_leader()
        self.leader_port = self.ports[self.leader]
        print(f"Epoch {epoch}: Initiating block proposal by leader node {self.leader}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            strat_propose_message = Message.create_start_proposal_message(epoch, self.leader)
            sock.connect(('localhost', self.leader_port))
            sock.sendall(strat_propose_message.serialize())

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
                    display_message = Message.create_display_blockchain_message(None, sender=0)
                    sock.sendall(display_message.serialize())
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

    def generate_random_transaction(self):
        """
        Creates a random transaction and sends it to a randomly selected node in the network.
        """
        sender = f"Client{random.randint(1, 100)}"
        receiver = f"Client{random.randint(1, 100)}"
        amount = random.randint(1, 1000)

        # Generate a unique transaction ID
        tx_id = self.get_next_tx_id()
        transaction = {
            'sender': sender,
            'receiver': receiver,
            'tx_id': tx_id,
            'amount': amount
        }

        # Send transaction to a random node
        target_port = random.choice(self.ports)
        transaction_message = Message.create_transaction_message(transaction, 0)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', target_port))
                s.sendall(transaction_message.serialize())
            print(f"Sent transaction {tx_id} from {sender} to {receiver} for {amount} coins to Node at port {target_port}.")
        except ConnectionRefusedError:
            print(f"Failed to send transaction to Node at port {target_port}.")

    def generate_transactions_periodically(self, interval):
        """
        Generates transactions at regular intervals and distributes them to random nodes.

        :param interval: int - The interval in seconds between each transaction generation.
        """
        while self.generate_transactions:
            self.generate_random_transaction()
            time.sleep(interval)
