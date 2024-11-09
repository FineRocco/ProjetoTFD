import threading
import socket
import time
import random
import hashlib
import json
import logging

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
        logging.info(f"Initialized Node {self.node_id} on port {self.port}")  # Use logging instead of print
        self.running = True
        self.lock = threading.Lock()

        # Initialize genesis block
        genesis_block = Block(
            epoch=0,
            previous_hash=b'0' * 20,
            transactions=[]
        )
        genesis_block.hash = genesis_block.compute_hash()
        self.blockchain.append(genesis_block)
        self.notarized_blocks[0] = genesis_block
        logging.info(f"Node {self.node_id} initialized with genesis block {genesis_block.hash.hex()}.")

    def propose_block(self, epoch, leader_id):
        """
        Proposes a new block at the start of an epoch if the node is the leader.

        :param epoch: int - The current epoch number.
        :param leader_id: int - The ID of the current leader node.
        :return: Block - The proposed block if the node is the leader, otherwise None.
        """
        if self.node_id != leader_id:
            logging.info(f"Node {self.node_id} is not the leader for epoch {epoch}.")
            return None

        latest_block = self.get_latest_notarized_block()
        previous_hash = latest_block.hash if latest_block else b'0' * 20

        with self.lock:
            # Copy the current pending transactions to the block
            block_transactions = list(self.pending_transactions)
            new_block = Block(
                epoch=epoch,
                previous_hash=previous_hash,
                transactions=block_transactions
            )
            new_block.hash = new_block.compute_hash()
            self.pending_transactions = []  # Clear pending transactions

        logging.info(f"Node {self.node_id} proposes Block: {new_block.hash.hex()} in epoch {epoch}")

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
        latest_notarized_block = self.get_latest_notarized_block()
        if latest_notarized_block and block.epoch <= latest_notarized_block.epoch:
            logging.info(f"Node {self.node_id} sees that block {block.hash.hex()} is not extending the chain.")
            return  # Do not vote for shorter or equal-length chains
        
        with self.lock:
            if block.epoch not in self.votes:
                self.votes[block.epoch] = []

            # Ensure each node votes only once per block
            if any(voted_block.hash == block.hash for voted_block in self.votes[block.epoch]):
                logging.info(f"Node {self.node_id} has already voted for Block {block.hash.hex()} in epoch {block.epoch}")
                return

            # Add vote and broadcast to others
            self.votes[block.epoch].append(block)
            block.votes += 1
            logging.info(f"Node {self.node_id} voted for Block {block.hash.hex()} in epoch {block.epoch}")
        
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
                logging.info(f"Block {block.hash.hex()} has already been notarized in epoch {block.epoch}")
                return

            # Notarize and broadcast if votes exceed threshold
            if block.votes > self.total_nodes // 2:
                self.notarized_blocks[block.epoch] = block
                logging.info(f"Node {self.node_id}: Block {block.hash.hex()} notarized in epoch {block.epoch}")
                
                echo_message = Message.create_echo_notarize_message(block, self.node_id)
                self.broadcast_message(echo_message)
                self.finalize_blocks()

    def finalize_blocks(self):
        """
        Finalizes blocks when three consecutive blocks are notarized.
        """
        logging.info(f"Node {self.node_id}: Checking for finalization...")
        notarized_epochs = sorted(self.notarized_blocks.keys())
        
        for i in range(2, len(notarized_epochs)):
            # Check for three consecutive notarized epochs
            if notarized_epochs[i] == notarized_epochs[i - 1] + 1 and notarized_epochs[i - 1] == notarized_epochs[i - 2] + 1:
                finalized_block = self.notarized_blocks[notarized_epochs[i]]
                if finalized_block not in self.blockchain:
                    logging.info(f"Node {self.node_id}: Finalizing Block {finalized_block.hash.hex()} in epoch {finalized_block.epoch}")
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
            parent_block = next(
                (b for b in self.notarized_blocks.values() if b.hash == current_block.previous_hash), None
            )
            current_block = parent_block
        return chain

    def get_latest_notarized_block(self):
        """
        Returns the last block in the longest notarized chain.

        :return: Block - The tip of the longest notarized chain.
        """
        with self.lock:
            if not self.notarized_blocks:
                return None  # No notarized blocks available yet

            # Find the block with the highest epoch
            latest_epoch = max(self.notarized_blocks.keys())
            return self.notarized_blocks[latest_epoch]

    def add_block(self, block):
        """
        Adds a proposed block to the node's set of blocks. Actual addition to the blockchain occurs upon notarization.

        :param block: Block - The proposed block.
        """
        with self.lock:
            latest_block = self.get_latest_notarized_block()
            if not latest_block:
                logging.info(f"Node {self.node_id}: No notarized blocks available to validate Block {block.hash.hex()}.")
                return

            if block.previous_hash != latest_block.hash:
                logging.info(f"Node {self.node_id}: Block {block.hash.hex()} has invalid previous hash. Expected {latest_block.hash.hex()}.")
                return

            # Optionally, store the block for future reference or validation
            # Here, we rely on notarization to add it to the blockchain
            logging.info(f"Node {self.node_id}: Received and validated Block {block.hash.hex()} for epoch {block.epoch}.")

    def add_transaction(self, transaction):
        """
        Adds a transaction to the node's pending transactions list.

        :param transaction: Transaction - The transaction to add.
        """
        with self.lock:
            self.pending_transactions.append(transaction)
        logging.info(f"Node {self.node_id} added transaction {transaction.tx_id} to pending transactions.")
    
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
                        logging.info(f"Node {self.node_id} broadcasting to port {target_port}")
                        s.connect(('localhost', target_port))
                        s.sendall(serialized_message)
                except ConnectionRefusedError:
                    logging.error(f"Node {self.node_id} could not connect to Node at port {target_port}")

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
            print(f"  Previous Hash: {block.previous_hash.hex()}")
            print(f"  Epoch: {block.epoch}")
            print(f"  Transactions: {len(block.transactions)} transactions")

            # Print each transaction in the block
            for tx in block.transactions:
                print(f"    Transaction {tx.tx_id}: from {tx.sender} to {tx.receiver} of {tx.amount} coins")
            print("-" * 40)  # Separator for each block

    def run(self):
        """
        The main loop for the node thread to handle incoming messages.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('localhost', self.port))
            sock.listen()
            logging.info(f"Node {self.node_id} listening on port {self.port}")

            while self.running:
                try:
                    conn, addr = sock.accept()
                    with conn:
                        data = conn.recv(4096)
                        if not data:
                            continue
                        message = Message.deserialize(data)
                        if not message:
                            logging.warning(f"Node {self.node_id} received invalid message.")
                            continue

                        logging.info(f"Node {self.node_id} received message: {message.type}")

                        if message.type == MessageType.PROPOSE:
                            block = message.content
                            self.vote_on_block(block)
                        elif message.type == MessageType.VOTE:
                            block = message.content
                            self.notarize_block(block)
                        elif message.type == MessageType.ECHO_NOTARIZE:
                            block = message.content
                            self.notarize_block(block)
                        elif message.type == MessageType.TRANSACTION:
                            tx_data = message.content
                            transaction = Transaction.from_dict(tx_data)
                            self.add_transaction(transaction)
                        elif message.type == MessageType.ECHO_TRANSACTION:
                            tx_data = message.content
                            transaction = Transaction.from_dict(tx_data)
                            self.add_transaction(transaction)
                        elif message.type == MessageType.DISPLAY_BLOCKCHAIN:
                            self.display_blockchain()
                        else:
                            logging.warning(f"Node {self.node_id} received unknown message type: {message.type}")

                except Exception as e:
                    logging.error(f"Node {self.node_id} encountered an error: {e}")

