import random
import socket
import threading
import time
from message import Message, MessageType
from node import Node
from block import Block
from transaction import Transaction
import subprocess

class StreamletNetwork:
    def __init__(self, num_nodes, delta, base_port):
        """
        Initializes a network with multiple nodes.
        
        :param num_nodes: The number of nodes in the network.
        :param delta: The network delay parameter (∆), which will determine epoch duration.
        """
        self.num_nodes = num_nodes
        self.leader = 0  # Initially, node 0 is the leader
        self.leader_port = 0
        self.global_tx_id = 0  # Global transaction counter
        self.tx_id_lock = threading.Lock()  # Lock to synchronize transaction ID generation
        self.delta = delta  # Set ∆, the network delay parameter
        self.epoch_duration = 2 * delta  # Epoch lasts for 2∆ rounds
        self.processes = []  # To store Popen process references
        # Node ports
        
        self.ports = [base_port + i for i in range(num_nodes)]
        print("port", self.ports)

        self.transaction_thread = None  # To store the transaction generation thread
        self.generate_transactions = True  # Flag to control transaction generation

        # Initialize the genesis block (epoch, length, and hash are all 0)
        self.genesis_block = Block(epoch=0, previous_hash=b'0', transactions=[])
        for node in self.processes:
            node.blockchain.append(self.genesis_block)  # Start all nodes with the genesis block
            node.notarized_blocks[0] = self.genesis_block  # Genesis block is notarized from the start

    def start_network(self):
        ready_port = 6000  # Port for readiness signaling
        ready_count = 0

        # Start each node process in a new terminal
        for i in range(self.num_nodes):
            node_port = self.ports[i]
            # Convert the list of ports to a comma-separated string to pass via command line
            port_list = ",".join(map(str, self.ports))
            process = subprocess.Popen(
                ["python", "node_script.py", str(i), str(self.num_nodes), str(node_port), port_list],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.processes.append(process)

        # Listen for readiness signals
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
        self.transaction_thread.daemon = True  # Daemon thread will close when the main program exits
        self.transaction_thread.start()
        print("Transaction generation thread started.")


    def stop_network(self):
        """
        Stops all nodes from running and stops transaction generation.
        """
        # Stop transaction generation
        self.generate_transactions = False
        if self.transaction_thread:
            self.transaction_thread.join()  # Wait for the transaction thread to finish

        # Terminate each node process and wait for it to close
        for process in self.processes:
            process.terminate()  # Send a termination signal to the subprocess
            process.wait()  # Wait for the process to finish
        print("All nodes and transaction generation thread stopped.")

    def next_leader(self):
        """
        Rotates the leader for the next epoch.
        """
        self.leader = (self.leader + 1) % self.num_nodes
        print("leader", self.leader)

    def start_epoch(self, epoch):
        """
        Starts a new epoch in the network where the leader proposes a block.
        
        :param epoch: The current epoch number.
        """
        self.next_leader()
        self.leader_port = self.ports[self.leader]
        print(f"Epoch {epoch}: Sending PROPOSE command to leader node {self.leader}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            strat_propose_message = Message.create_start_proposal_message(epoch, self.leader)
            sock.connect(('localhost', self.leader_port))
            sock.sendall(strat_propose_message.serialize())

    def run(self, total_epochs):
        for epoch in range(1, total_epochs + 1):
            print(f"=== Epoch {epoch} ===")
            self.start_epoch(epoch)

            time.sleep(self.epoch_duration)
        
        print("\n=== Final Blockchain for each node ===")

    def get_next_tx_id(self):
        """
        Provides a globally unique transaction ID.
        
        :return: The next available transaction ID.
        """
        with self.tx_id_lock:
            self.global_tx_id += 1
            return self.global_tx_id
        
    def generate_random_transaction(self):
        sender = f"Client{random.randint(1, 100)}"
        receiver = f"Client{random.randint(1, 100)}"
        amount = random.randint(1, 1000)

        # Generate a unique transaction ID
        tx_id = self.get_next_tx_id()
        transaction = {
            'tx_id': tx_id,
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        }

        # Choose a random node's port
        target_port = random.choice(self.ports)

        # Send the transaction to the target node via a socket
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
        Generates transactions at regular intervals.
        """
        while self.generate_transactions:
            self.generate_random_transaction()
            time.sleep(interval)
