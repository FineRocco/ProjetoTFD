import threading
import socket
import time
import random

from block import Block
from message import Message, MessageType
from transaction import Transaction

class Node(threading.Thread):
    """
    Represents a blockchain node in a network running the Streamlet consensus protocol.
    Each node can propose, vote, and notarize blocks, and broadcasts messages to other nodes.
    """
    
    def __init__(self, node_id, total_nodes, network, port, ports):
        """
        Initializes a Node object and starts a thread for it.

        :param node_id: int - The unique ID of the node.
        :param total_nodes: int - Total number of nodes in the network.
        :param network: Network object - The network object to facilitate communication between nodes.
        :param port: int - The network port the node listens to.
        :param ports: list - The list of all valid ports in the network.
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
        self.ports = ports  # List of all valid node ports
        print(f"Initialized Node {self.node_id} on port {self.port}")  # Debug print
        self.running = True
        self.lock = threading.Lock()

    def propose_block(self, epoch, leader_id):
        """
        Proposes a new block at the start of an epoch if the node is the leader.

        :param epoch: int - The current epoch number.
        :param leader_id: int - The ID of the current leader node.
        :return: Block - The proposed block if the node is the leader, otherwise None.
        """
        if self.node_id != leader_id:
            print(f"Node {self.node_id} is not the leader for epoch {epoch}.")
            return None

        previous_block = self.get_longest_notarized_chain()
        previous_hash = previous_block.hash if previous_block else b'0' * 20

        with self.lock:
            # Copy the current pending transactions to the block
            block_transactions = list(self.pending_transactions)
            new_block = Block(epoch, previous_hash, block_transactions)
            self.pending_transactions = []  # Clear pending transactions

        print(f"Node {self.node_id} proposes Block: {new_block.hash.hex()}")
        
        # Create a Propose message and broadcast it
        propose_message = Message.create_propose_message(new_block, self.node_id)
        self.broadcast_message(propose_message)
        return new_block

    def vote_on_block(self, block):
        """
        Votes on a proposed block if it extends the longest notarized chain.

        :param block: Block - The proposed block.
        :return: Message - A vote message for the block.
        """
        longest_notarized_block = self.get_longest_notarized_chain()
        if longest_notarized_block and block.length <= longest_notarized_block.length:
            return  # Do not vote for shorter or equal-length chains
        
        with self.lock:
            if block.epoch not in self.votes:
                self.votes[block.epoch] = []

            # Ensure each node votes only once per block
            if any(voted_block.hash == block.hash for voted_block in self.votes[block.epoch]):
                print(f"Node {self.node_id} has already voted for Block {block.hash.hex()} in epoch {block.epoch}")
                return

            # Add vote and broadcast to others
            self.votes[block.epoch].append(block)
            block.votes += 1
            print(f"Node {self.node_id} voted for Block {block.hash.hex()} in epoch {block.epoch}")
        
        # Create and broadcast vote message
        vote_message = Message.create_vote_message(block, self.node_id)
        self.broadcast_message(vote_message)
        return vote_message

    def notarize_block(self, block):
        """
        Notarizes a block if it receives more than n/2 votes, and notifies other nodes.

        :param block: Block - The block to notarize.
        """
        with self.lock:
            if block.epoch in self.notarized_blocks and self.notarized_blocks[block.epoch].hash == block.hash:
                print(f"Block {block.hash.hex()} has already been notarized in epoch {block.epoch}")
                return

            # Notarize and broadcast if votes exceed threshold
            if block.votes > self.total_nodes // 2:
                self.notarized_blocks[block.epoch] = block
                print(f"Node {self.node_id}: Block {block.hash.hex()} notarized in epoch {block.epoch}")
                
                echo_message = Message.create_echo_notarize_message(block, self.node_id)
                self.broadcast_message(echo_message)
                self.finalize_blocks()

    def finalize_blocks(self):
        """
        Finalizes blocks when three consecutive blocks are notarized.
        """
        print(f"Node {self.node_id}: Checking for finalization...")
        notarized_epochs = sorted(self.notarized_blocks.keys())
        
        for i in range(1, len(notarized_epochs) - 1):
            # Check for three consecutive notarized epochs
            if notarized_epochs[i] == notarized_epochs[i - 1] + 1 and notarized_epochs[i + 1] == notarized_epochs[i] + 1:
                finalized_block = self.notarized_blocks[notarized_epochs[i]]
                if finalized_block not in self.blockchain:
                    print(f"Node {self.node_id}: Finalizing Block {finalized_block.hash.hex()} in epoch {finalized_block.epoch}")
                    chain = self.get_chain_to_block(finalized_block)
                    self.blockchain.extend(chain)

    def get_chain_to_block(self, block):
        """
        Helper function to retrieve the entire parent chain up to the specified block.

        :param block: Block - The target block.
        :return: list - The chain of blocks up to and including the target block.
        """
        chain = []
        current_block = block
        while current_block and current_block not in self.blockchain:
            chain.insert(0, current_block)
            current_block = next(
                (b for b in self.notarized_blocks.values() if b.hash == current_block.previous_hash), None
            )
        return chain

    def get_longest_notarized_chain(self):
        """
        Returns the last block in the longest notarized chain, traversing backwards from the latest epoch.

        :return: Block - The tip of the longest notarized chain.
        """
        with self.lock:
            if not self.notarized_blocks:
                return None # No notarized blocks available yet

             # Start with the latest epoch's block as the tip of the chain
            latest_epoch = max(self.notarized_blocks.keys())
            longest_chain_tip = self.notarized_blocks[latest_epoch]

            # Traverse backwards through the chain
            chain = []
            current_block = longest_chain_tip   

        while current_block:
            chain.append(current_block)
            parent_block = None
            with self.lock:
                for block in self.notarized_blocks.values():
                    if block.hash == current_block.previous_hash:
                        parent_block = block
                        break
             # Move to the parent or break if no parent is found (likely genesis)
            if parent_block:
                current_block = parent_block
            else:
                break

        # Return the tip (most recent block in the notarized chain)
        return chain[-1] if chain else None

    def add_transaction(self, transaction):
        """
        Adds a transaction to the node's pending transactions list.

        :param transaction: Transaction - The transaction to add.
        """
        with self.lock:
            self.pending_transactions.append(transaction)
        print(f"Node {self.node_id} added transaction {transaction.tx_id} to pending transactions.")
    
    def broadcast_message(self, message):
        """
        Broadcasts a message to all other nodes.

        :param message: Message - The message to broadcast.
        """
        serialized_message = message.serialize()
        for target_port in self.ports:
            if target_port != self.port:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        print(f"Node {self.node_id} broadcasting to port {target_port}")
                        s.connect(('localhost', target_port))
                        s.sendall(serialized_message)
                except ConnectionRefusedError:
                    print(f"Node {self.node_id} could not connect to Node at port {target_port}")
    
    def display_blockchain(self):
        """
        Displays the current state of the blockchain for this node, including each block and its transactions.
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
            print(f"  Transactions: {block.length} transactions")

            # Print each transaction in the block
            for tx in block.transactions:
                print(f"    Transaction {tx.tx_id}: from {tx.sender} to {tx.receiver} of {tx.amount} coins")
            print("-" * 40)  # Separator for each block
