import threading
import socket
import time
import random

from block import Block
from message import Message, MessageType
from transaction import Transaction

class Node(threading.Thread):
    def __init__(self, node_id, total_nodes, network, port):
        """
        Initializes a Node object and starts a thread for it.

        :param node_id: The unique ID of the node.
        :param total_nodes: Total number of nodes in the network.
        :param network: The network object to facilitate communication between nodes.
        """
        threading.Thread.__init__(self)
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.blockchain = []  # Local chain of notarized blocks
        self.pending_transactions = []
        self.votes = {}  # Keeps track of votes for each block by epoch
        self.notarized_blocks = {}  # Blocks that received n/2 votes
        self.network = network
        self.port = port
        self.running = True
        self.lock = threading.Lock()

    def run(self):
        # Accept incoming connections and start a listener thread for each connection
        while self.running:
            conn, addr = self.sock.accept()
            threading.Thread(target=self.handle_connection, args=(conn,)).start()

    def handle_connection(self, conn):
        # Handle incoming messages from other nodes
        while self.running:
            try:
                data = conn.recv(4096)
                if data:
                    message = Message.deserialize(data)  # Assuming Message class has deserialize method
                    self.receive_message(message)
            except ConnectionResetError:
                break

    def propose_block(self, epoch):
        """
        Proposes a new block at the start of an epoch.
        :param epoch: The current epoch number.
        """
        if self.node_id != self.network.leader:
            print(f"Node {self.node_id} is not the leader for epoch {epoch}.")
            return None
        
        previous_block = self.get_longest_notarized_chain()
        previous_hash = previous_block.hash if previous_block else b'0' * 20

        with self.lock:
            new_block = Block(epoch, previous_hash, self.pending_transactions)
            self.pending_transactions = []

        print(f"Node {self.node_id} proposes Block: {new_block.hash.hex()}")
        
        # Create a Propose message
        propose_message = Message.create_propose_message(new_block, self.node_id)

        # Broadcast the Propose message to all other nodes
        self.broadcast_message(propose_message)

        return new_block

    def vote_on_block(self, block):
        """
        Votes on a proposed block if it extends the longest notarized chain.
        
        :param block: The proposed block.
        :return: A vote message.
        """
        longest_notarized_block = self.get_longest_notarized_chain()
        if longest_notarized_block and block.length <= longest_notarized_block.length:
            return  # Do not vote for shorter or equal-length chains
        
        with self.lock:
            # Ensure that the votes list for this epoch is initialized
            if block.epoch not in self.votes:
                self.votes[block.epoch] = []

            # Check if this node has already voted for this block in this epoch
            if any(voted_block.hash == block.hash for voted_block in self.votes[block.epoch]):
                print(f"Node {self.node_id} has already voted for Block {block.hash.hex()} in epoch {block.epoch}")
                return  # Node has already voted for this block in this epoch

            # Add the block to the list of voted blocks for this epoch
            self.votes[block.epoch].append(block)
            block.votes += 1  # Increment the block's vote count
            print(f"Node {self.node_id} voted for Block {block.hash.hex()} in epoch {block.epoch}")

        # Broadcast vote to all other nodes
        vote_message = Message.create_vote_message(block, self.node_id)
        self.broadcast_message(vote_message)
        
        return vote_message

    def notarize_block(self, block):
        """
        Notarizes a block if it receives more than n/2 votes.
        
        :param block: The block to notarize.
        """
        #epoch_votes = self.votes.get(block.epoch, [])
        #unique_vote_count = len({b.hash for b in epoch_votes})  # Count unique votes by block hash

        with self.lock:
            if block.epoch in self.notarized_blocks and self.notarized_blocks[block.epoch].hash == block.hash:
                print(f"Block {block.hash.hex()} has already been notarized in epoch {block.epoch}")
                return  # Block has already been notarized

            # Notarize the block if it has more than n/2 votes
            if block.votes > self.total_nodes // 2:
                self.notarized_blocks[block.epoch] = block
                print(f"Block {block.hash.hex()} notarized in epoch {block.epoch}")
        
        self.finalize_blocks()


    def finalize_blocks(self):
        """
        Finalizes blocks when three consecutive blocks are notarized.
        """
        with self.lock:
            # Finalize logic: three consecutive notarized blocks
            notarized_epochs = sorted(self.notarized_blocks.keys())
            for i in range(1, len(notarized_epochs) - 1):
                if notarized_epochs[i] == notarized_epochs[i-1] + 1 and notarized_epochs[i+1] == notarized_epochs[i] + 1:
                    # Finalize the second block in this sequence
                    finalized_block = self.notarized_blocks[notarized_epochs[i]]
                    print(f"Node {self.node_id} finalizes Block {finalized_block.hash.hex()}")
                    self.blockchain.append(finalized_block)

    def broadcast_message(self, message):
        serialized_message = message.serialize()  # Assuming Message class has serialize method
        for node in self.network.nodes:
            if node.node_id != self.node_id:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        print("Socket connection node class" + node.port)
                        s.connect(('localhost', node.port))
                        s.sendall(serialized_message)
                except ConnectionRefusedError:
                    print(f"Node {self.node_id} could not connect to Node {node.node_id}")


    def get_longest_notarized_chain(self):
        """
        Returns the last block in the longest notarized chain.
        Traverses from the latest notarized block backwards to find the longest chain.
        """
        with self.lock:  # Acquire the lock to safely access shared resources
            if not self.notarized_blocks:
                return None  # No notarized blocks yet

            # Find the latest epoch with a notarized block
            latest_epoch = max(self.notarized_blocks.keys())
            longest_chain_tip = self.notarized_blocks[latest_epoch]

            # Traverse backward through the chain to form the full notarized chain
            chain = []
            current_block = longest_chain_tip

        while current_block:
            chain.append(current_block)

            # Find the parent block by matching its hash with the previous hash (in bytes)
            parent_block = None
            with self.lock:  # Lock again just while accessing notarized_blocks
                for block in self.notarized_blocks.values():
                    if block.hash == current_block.previous_hash:
                        parent_block = block
                        break

            current_block = parent_block

        # Return the tip of the longest notarized chain (the last block added to the chain)
        return chain[-1] if chain else None
    
    def display_blockchain(self):
        """
        Displays the current state of the blockchain for this node.
        """
        if not self.blockchain:
            print(f"Node {self.node_id}: Blockchain is empty.")
            return
    
        print(f"Node {self.node_id}: Current Blockchain:")
        for index, block in enumerate(self.blockchain):
            print(f"Block {index + 1}:")
            print(f"  Hash: {block.hash.hex()}")
            print(f"  Previous Hash: {block.previous_hash}")
            print(f"  Epoch: {block.epoch}")
            print(f"  Transactions: {len(block.transactions)} transactions")
            for tx in block.transactions:
                print(f"    Transaction {tx.tx_id}: from {tx.sender} to {tx.receiver} of {tx.amount} coins")
            print("-" * 40)  # Separator for each block

