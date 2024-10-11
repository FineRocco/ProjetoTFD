import random
import threading
import time
from message import Message, MessageType
from node import Node
from block import Block
from transaction import Transaction

class StreamletNetwork:
    def __init__(self, num_nodes, delta):
        """
        Initializes a network with multiple nodes.
        
        :param num_nodes: The number of nodes in the network.
        :param delta: The network delay parameter (∆), which will determine epoch duration.
        """
        self.num_nodes = num_nodes
        self.nodes = [Node(node_id=i, total_nodes=num_nodes, network=self) for i in range(num_nodes)]
        self.leader = 0  # Initially, node 0 is the leader
        self.global_tx_id = 0  # Global transaction counter
        self.tx_id_lock = threading.Lock()  # Lock to synchronize transaction ID generation
        self.delta = delta  # Set ∆, the network delay parameter
        self.epoch_duration = 2 * delta  # Epoch lasts for 2∆ rounds

        # Initialize the genesis block (epoch, length, and hash are all 0)
        self.genesis_block = Block(epoch=0, previous_hash=b'0', transactions=[])
        for node in self.nodes:
            node.blockchain.append(self.genesis_block)  # Start all nodes with the genesis block
            node.notarized_blocks[0] = self.genesis_block  # Genesis block is notarized from the start

    def start_network(self):
        """
        Starts all the nodes as separate threads.
        """
        for node in self.nodes:
            node.start()

        # Start generating transactions periodically in a separate thread
        transaction_thread = threading.Thread(target=self.generate_transactions_periodically, args=(self.delta/2,))
        transaction_thread.daemon = True  # Daemon thread will exit when the main program exits
        transaction_thread.start()

    def stop_network(self):
        """
        Stops all nodes from running.
        """
        for node in self.nodes:
            node.running = False
            node.join()  # Wait for the thread to finish

    def next_leader(self):
        """
        Rotates the leader for the next epoch.
        """
        self.leader = (self.leader + 1) % len(self.nodes)

    def start_epoch(self, epoch):
        """
        Starts a new epoch in the network where the leader proposes a block.
        
        :param epoch: The current epoch number.
        """
        leader_node = self.nodes[self.leader]
        proposed_block = leader_node.propose_block(epoch)
        message = Message(MessageType.PROPOSE, proposed_block, leader_node.node_id)

        # Broadcast the proposed block to all other nodes
        for node in self.nodes:
            if node.node_id != leader_node.node_id:
                node.receive_message(message)

    def run(self, total_epochs):
        """
        Runs the consensus protocol for a number of epochs.
        
        :param total_epochs: The number of epochs to run.
        """
        for epoch in range(1, total_epochs + 1):
            print(f"=== Epoch {epoch} ===")
            self.start_epoch(epoch)
            # Rotate leader
            self.next_leader()

            # Finalize blocks at each node
            for node in self.nodes:
                node.finalize_blocks()

            # Wait for the epoch duration (2∆) before starting the next epoch
            time.sleep(self.epoch_duration)
        
        # After all epochs have completed, print the final blockchain for each node
        print("\n=== Final Blockchain for each node ===")
        for node in self.nodes:
            node.display_blockchain()

    def get_next_tx_id(self):
        """
        Provides a globally unique transaction ID.
        
        :return: The next available transaction ID.
        """
        with self.tx_id_lock:
            self.global_tx_id += 1
            return self.global_tx_id
        
    def generate_random_transaction(self):
        """
        Generates a random transaction with a unique transaction ID and distributes
        it to a random node in the network.
        """
        sender = f"Client{random.randint(1, 100)}"
        receiver = f"Client{random.randint(1, 100)}"
        amount = random.randint(1, 1000)

        # Get a globally unique transaction ID
        tx_id = self.get_next_tx_id()
        transaction = Transaction(tx_id, sender, receiver, amount)

        # Distribute the transaction to a random node in the network
        target_node = random.choice(self.nodes)
        target_node.pending_transactions.append(transaction)
        print(f"Transaction {tx_id} generated: {sender} -> {receiver}, Amount: {amount}, assigned to Node {target_node.node_id}")
    
    def generate_transactions_periodically(self, interval):
        """
        Generates transactions at regular intervals.
        """
        while True:
            self.generate_random_transaction()
            time.sleep(interval)
