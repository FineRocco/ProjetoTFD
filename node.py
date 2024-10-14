import hashlib
import threading
from blockchain import Blockchain, Block
from message import Message
from transaction import Transaction

class Node:
    def __init__(self, node_id, blockchain):
        self.node_id = node_id  # Unique identifier for the node
        self.blockchain = blockchain  # Each node has its own blockchain instance
        self.pending_transactions = []  # Transactions waiting to be included in a block
        self.current_epoch = 0   # Current epoch number
        self.votes = {}          # Dictionary to track votes for blocks
        self.leader = False      # Indicates if the node is the leader for the current epoch
        self.peers = []          # List of peers connected to this node
        self.message_thread = threading.Thread(target=self.process_messages)
        self.message_thread.start()

    def __repr__(self):
        return f"Node {self.node_id}, Epoch: {self.current_epoch}, Leader: {self.leader}, Blockchain Length: {len(self.blockchain.blocks)}"

    def process_message(self, message):
        """Process received messages."""
        if message.msg_type == "Propose":
            self.vote_block(message.content)  # Vote for the proposed block
        elif message.msg_type == "Vote":
            self.notarize_block_votes(message.content)  # Track votes

    def propose_block(self):
        """Propose a new block if the node is the leader."""
        if not self.leader:
            print(f"Node {self.node_id} is not the leader for epoch {self.current_epoch}.")
            return

        new_block = Block(
            previous_hash=self.blockchain.blocks[-1].calculate_hash(),
            epoch=self.current_epoch,
            length=len(self.blockchain.blocks) + 1,
            header="Block Header",
            transactions=self.pending_transactions
        )

        print(f"Node {self.node_id} proposed block for epoch {self.current_epoch}.")
        self.broadcast(Message(msg_type="Propose", content=new_block, sender=self.node_id))

    def vote_block(self, block):
        """Vote for a proposed block."""
        if not block.transactions:
            print(f"Node {self.node_id} cannot vote for an empty block.")
            return

        self.blockchain.add_block(block)  # Add block to the blockchain
        print(f"Node {self.node_id} voted for block {block.length} in epoch {self.current_epoch}.")
        self.broadcast(Message(msg_type="Vote", content=block, sender=self.node_id))

    def notarize_block_votes(self, block):
        """Notarize the block if enough votes are received."""
        if block not in self.votes:
            self.votes[block] = 0
        self.votes[block] += 1

        if self.votes[block] > len(self.peers) / 2:  # Majority vote
            self.blockchain.notarize_block(block)
            print(f"Block {block.length} in epoch {block.epoch} notarized by Node {self.node_id}.")
            self.finalize()

    def finalize(self):
        """Finalize the block if all conditions are met."""
        self.blockchain.finalize()
        print(f"Node {self.node_id} finalized blockchain in epoch {self.current_epoch}.")
    
    def get_current_epoch(self):
        """Returns the current epoch for the node."""
        return self.current_epoch

    def update_current_leader(self, nodes_count):
        """
        Node finds the epoch leader using a hash-based method.
        Leader calculation is based on the number of nodes in the network.
        """
        epoch = self.get_current_epoch()
        hasher = hashlib.sha256()  # Using sha256 hash function
        hasher.update(str(epoch).encode('utf-8'))  # Hash the epoch as a string
        epoch_hash = int(hasher.hexdigest(), 16)  # Convert the hash to an integer

        return epoch_hash % nodes_count  # Leader is determined by modulus

    def broadcast(self, message):
        """Broadcast messages to peers."""
        for peer in self.peers:
            peer.process_message(message)
            print(f"Node {self.node_id} broadcasted message to Node {peer.node_id}.")

    def add_transaction(self, transaction):
        """Add transaction to pending transactions if valid."""
        if isinstance(transaction, Transaction) and transaction.is_valid():
            self.pending_transactions.append(transaction)
            print(f"Node {self.node_id} added transaction {transaction.transaction_id}.")
        else:
            print(f"Invalid transaction: {transaction}.")
