import threading
import time
import random
import hashlib
from collections import defaultdict
import queue

# Constants
NUM_NODES = 5
EPOCH_DURATION = 2  # seconds
D = 1  # Maximum network delay in epochs
MAJORITY = (NUM_NODES // 2) + 1

# Data Structures

class Transaction:
    """Represents a transaction in the network."""
    def __init__(self, sender, receiver, transaction_id, amount):
        self.sender = sender
        self.receiver = receiver
        self.transaction_id = transaction_id
        self.amount = amount

    def __repr__(self):
        return f"Tx{self.transaction_id}({self.sender}->{self.receiver}, ${self.amount})"

class Block:
    """Represents a block in the blockchain."""
    def __init__(self, previous_hash, epoch, length, transactions):
        self.previous_hash = previous_hash
        self.epoch = epoch
        self.length = length
        self.transactions = transactions
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = f"{self.previous_hash}{self.epoch}{self.length}{[str(tx) for tx in self.transactions]}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def __repr__(self):
        return f"Block(Epoch: {self.epoch}, Length: {self.length}, Hash: {self.hash[:6]})"

class Message:
    """Represents a message exchanged between nodes."""
    def __init__(self, msg_type, content, sender_id):
        self.type = msg_type  # 'PROPOSE', 'VOTE'
        self.content = content
        self.sender_id = sender_id

    def __repr__(self):
        return f"Message({self.type} from Node {self.sender_id})"

# Node Implementation

class Node(threading.Thread):
    """Represents a node in the network."""
    def __init__(self, node_id, nodes):
        super().__init__()
        self.node_id = node_id
        self.nodes = nodes  # Reference to all nodes
        self.message_queue = queue.Queue()
        self.blockchain = {}  # Key: Block hash, Value: Block
        self.pending_transactions = []
        self.received_votes = defaultdict(set)  # Key: Block hash, Value: Set of node_ids
        self.notarized_blocks = set()
        self.finalized_blocks = []
        self.current_epoch = 0
        self.is_active = True  # Indicates if the node is active (not crashed)

        # Initialize with genesis block
        genesis_block = Block('0', 0, 0, [])
        self.blockchain[genesis_block.hash] = genesis_block
        self.notarized_blocks.add(genesis_block.hash)
        self.latest_notarized_block = genesis_block

    def broadcast(self, message):
        """Sends a message to all other nodes."""
        if not self.is_active:
            return
        for node in self.nodes:
            if node.node_id != self.node_id and node.is_active:
                node.receive_message(message)
        print(f"Node {self.node_id}: Broadcasted {message.type} message.")

    def receive_message(self, message):
        """Receives a message from another node."""
        if not self.is_active:
            return
        self.message_queue.put(message)
        print(f"Node {self.node_id}: Received {message.type} message from Node {message.sender_id}.")

    def run(self):
        """Main loop of the node."""
        while self.is_active:
            epoch_start_time = time.time()
            self.current_epoch += 1
            leader_id = self.select_leader(self.current_epoch)
            print(f"Node {self.node_id}: Starting Epoch {self.current_epoch}. Leader is Node {leader_id}.")

            # Leader proposes a block
            if self.node_id == leader_id:
                self.propose_block()

            # Process incoming messages
            while time.time() - epoch_start_time < EPOCH_DURATION:
                try:
                    message = self.message_queue.get(timeout=0.1)
                    self.process_message(message)
                except queue.Empty:
                    continue

            # Finalize blocks if possible
            self.finalize_blocks()

            # Simulate node crash with a small probability
            if random.random() < 0.05:
                print(f"Node {self.node_id} has crashed.")
                self.is_active = False

    def select_leader(self, epoch):
        """Determines the leader for the current epoch."""
        return epoch % NUM_NODES

    def propose_block(self):
        """Leader creates and broadcasts a new block proposal."""
        parent_block = self.latest_notarized_block
        new_block = Block(
            previous_hash=parent_block.hash,
            epoch=self.current_epoch,
            length=parent_block.length + 1,
            transactions=self.collect_transactions()
        )
        self.blockchain[new_block.hash] = new_block
        proposal = Message('PROPOSE', new_block, self.node_id)
        self.broadcast(proposal)
        print(f"Node {self.node_id}: Proposed {new_block} with transactions {new_block.transactions}.")

    def collect_transactions(self):
        """Collects unconfirmed transactions."""
        transactions = self.pending_transactions.copy()
        self.pending_transactions.clear()
        return transactions

    def process_message(self, message):
        """Processes an incoming message."""
        if not self.is_active:
            return
        if message.type == 'PROPOSE':
            self.handle_proposal(message)
        elif message.type == 'VOTE':
            self.handle_vote(message)
        else:
            print(f"Node {self.node_id}: Unknown message type {message.type}")

    def handle_proposal(self, message):
        """Handles a received block proposal."""
        proposed_block = message.content
        # Verify the block extends the latest notarized block
        if self.verify_block(proposed_block):
            # Store the block
            self.blockchain[proposed_block.hash] = proposed_block
            print(f"Node {self.node_id}: Verified and stored proposed block {proposed_block}.")
            # Vote for the block
            vote = Message('VOTE', proposed_block.hash, self.node_id)
            self.broadcast(vote)
        else:
            print(f"Node {self.node_id}: Rejected proposed block {proposed_block}.")

    def verify_block(self, block):
        """Verifies that the block extends a notarized block."""
        parent_hash = block.previous_hash
        if parent_hash in self.notarized_blocks:
            return True
        return False

    def handle_vote(self, message):
        """Handles a received vote."""
        block_hash = message.content
        self.received_votes[block_hash].add(message.sender_id)
        print(f"Node {self.node_id}: Received vote for block {block_hash[:6]} from Node {message.sender_id}.")
        # Check if block is notarized
        if len(self.received_votes[block_hash]) >= MAJORITY and block_hash not in self.notarized_blocks:
            # Notarize the block
            self.notarized_blocks.add(block_hash)
            block = self.blockchain[block_hash]
            print(f"Node {self.node_id}: Block {block} is notarized.")
            # Update latest notarized block if necessary
            if block.length > self.latest_notarized_block.length or \
               (block.length == self.latest_notarized_block.length and block.hash < self.latest_notarized_block.hash):
                self.latest_notarized_block = block

    def finalize_blocks(self):
        """Finalizes blocks if three consecutive notarized blocks are found."""
        # Build the chain from the latest notarized block
        chain = []
        block = self.latest_notarized_block
        while block:
            chain.append(block)
            if block.previous_hash in self.blockchain:
                block = self.blockchain.get(block.previous_hash)
            else:
                block = None
        chain.reverse()
        # Finalize blocks if three consecutive notarized blocks are found
        for i in range(len(chain) - 2):
            b1 = chain[i]
            b2 = chain[i + 1]
            b3 = chain[i + 2]
            if b1.hash in self.notarized_blocks and b2.hash in self.notarized_blocks and b3.hash in self.notarized_blocks:
                if b1 not in self.finalized_blocks:
                    self.finalized_blocks.append(b1)
                    print(f"Node {self.node_id}: Finalized {b1}.")
        # Remove finalized transactions from pending list
        finalized_txs = set()
        for block in self.finalized_blocks:
            finalized_txs.update(block.transactions)
        self.pending_transactions = [tx for tx in self.pending_transactions if tx not in finalized_txs]

    def receive_transaction(self, transaction):
        """Receives a new transaction."""
        if not self.is_active:
            return
        self.pending_transactions.append(transaction)
        print(f"Node {self.node_id}: Received transaction {transaction}.")

# Simulation Environment

def simulate_phase1():
    """Runs the simulation for Phase 1."""
    # Initialize nodes
    nodes = [Node(node_id, None) for node_id in range(NUM_NODES)]
    for node in nodes:
        node.nodes = nodes  # Set reference to all nodes

    # Start nodes
    for node in nodes:
        node.start()

    # Simulate transaction generation
    transaction_id = 0
    try:
        while any(node.is_active for node in nodes):
            sender = random.randint(0, NUM_NODES - 1)
            receiver = random.randint(0, NUM_NODES - 1)
            amount = round(random.uniform(1.0, 100.0), 2)
            transaction = Transaction(sender, receiver, transaction_id, amount)
            transaction_id += 1
            # Broadcast transaction to all active nodes
            for node in nodes:
                if node.is_active:
                    node.receive_transaction(transaction)
            time.sleep(1)  # Adjust transaction rate as needed
    except KeyboardInterrupt:
        # Stop all threads gracefully
        print("Simulation stopped by user.")
        for node in nodes:
            node.join()

if __name__ == "__main__":
    simulate_phase1()
