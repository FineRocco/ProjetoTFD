import threading
import time
import random

from block import Block
from message import Message, MessageType
from transaction import Transaction

class Node(threading.Thread):
    def __init__(self, node_id, total_nodes, network):
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
        self.running = True
        self.lock = threading.Lock()
    
    def run(self):
        """
        The main loop of the node. Generates random transactions periodically.
        """
        while self.running:
            # Simulate random transaction generation
            self.generate_random_transaction()
            time.sleep(random.uniform(1, 3))  # Sleep for 1 to 3 seconds

    def generate_random_transaction(self):
        """
        Generates a random transaction and adds it to the pending transaction list.
        """
        sender = random.randint(0, self.total_nodes - 1)
        receiver = random.randint(0, self.total_nodes - 1)
        amount = round(random.uniform(1, 100), 2)

        if sender != receiver:
            tx_id = self.network.get_next_tx_id()  # Fetch globally unique ID
            tx = Transaction(sender, receiver, tx_id, amount)
            self.pending_transactions.append(tx)
            print(f"Node {self.node_id} generated transaction: {tx.tx_id}")

    def propose_block(self, epoch):
        """
        Proposes a new block at the start of an epoch.
        :param epoch: The current epoch number.
        """
        with self.lock:
            # Select the longest notarized chain
            previous_block = self.get_longest_notarized_chain()
            previous_hash = previous_block.hash if previous_block else '0'
            new_block = Block(epoch, previous_hash, self.pending_transactions)
            self.pending_transactions = []  # Clear after proposing
            print(f"Node {self.node_id} proposes Block: {new_block.hash}")
        
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
        if longest_notarized_block and block.chain_length <= longest_notarized_block.chain_length:
            return  # Do not vote for shorter or equal-length chains
        
        if block.epoch not in self.votes:
            self.votes[block.epoch] = []

        self.votes[block.epoch].append(block)
        print(f"Node {self.node_id} votes for Block {block.hash} in epoch {block.epoch}")

        # Broadcast vote to all other nodes
        vote_message = Message.create_vote_message(block, self.node_id)
        self.broadcast_message(vote_message)
        
        return vote_message

    def notarize_block(self, block):
        """
        Notarizes a block if it receives more than n/2 votes.
        
        :param block: The block to notarize.
        """
        epoch_votes = self.votes.get(block.epoch, [])
        if len(epoch_votes) > self.total_nodes // 2:
            self.notarized_blocks[block.epoch] = block
            print(f"Block {block.hash} notarized in epoch {block.epoch}")
            self.finalize_blocks()

    def finalize_blocks(self):
        """
        Finalizes blocks when three consecutive blocks are notarized.
        """
        # Finalize logic: three consecutive notarized blocks
        notarized_epochs = sorted(self.notarized_blocks.keys())
        for i in range(1, len(notarized_epochs) - 1):
            if notarized_epochs[i] == notarized_epochs[i-1] + 1 and notarized_epochs[i+1] == notarized_epochs[i] + 1:
                # Finalize the second block in this sequence
                finalized_block = self.notarized_blocks[notarized_epochs[i]]
                print(f"Node {self.node_id} finalizes Block {finalized_block.hash}")
                self.blockchain.append(finalized_block)

    def receive_message(self, message):
        """
        Handles incoming messages (Propose, Vote, Echo).
        
        :param message: The message received.
        """
        if message.msg_type == MessageType.PROPOSE:
            print(f"Node {self.node_id} received proposed Block {message.content.hash}")
            self.vote_on_block(message.content)

            # Send Echo message to other nodes after receiving a Propose message
            echo_message = Message.create_echo_message(message, self.node_id)
            self.broadcast_message(echo_message)

        elif message.msg_type == MessageType.VOTE:
            print(f"Node {self.node_id} received vote for Block {message.content.hash}")
            self.notarize_block(message.content)

            # Send Echo message to other nodes after receiving a Vote message
            echo_message = Message.create_echo_message(message, self.node_id)
            self.broadcast_message(echo_message)

        elif message.msg_type == MessageType.ECHO:
            print(f"Node {self.node_id} received echo for message from node {message.sender}")
            # Echo handling logic can be added here if needed

    def broadcast_message(self, message):
        """
        Sends a message to all other nodes in the network.
        
        :param message: The message to broadcast.
        """
        for node in self.network.nodes:
            if node.node_id != self.node_id:
                node.receive_message(message)


    def get_longest_notarized_chain(self):
        """
        Returns the last block in the longest notarized chain.
        Traverses from the latest notarized block backwards to find the longest chain.
        """
        # Start with the latest epoch with a notarized block
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
            # Find the parent block by matching its hash with the previous hash
            parent_block = None
            for block in self.notarized_blocks.values():
                if block.hash == current_block.previous_hash:
                    parent_block = block
                    break
            current_block = parent_block
        
        # Return the block at the tip of the longest notarized chain
        # which is the most recent block in the longest consecutive notarized chain
        return chain[-1] if chain else None
