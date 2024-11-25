# node.py
import threading
import socket
import time
import random
import hashlib
from datetime import datetime
from queue import Queue
from block import Block
from message import Message, MessageType
from transaction import Transaction

class Node(threading.Thread):
    """
    Represents a blockchain node in a network running the Streamlet consensus protocol.
    """

    def __init__(self, node_id, total_nodes, total_epochs, delta, port, ports, start_time):
        super().__init__()
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.total_epochs = total_epochs
        self.epoch_duration = 2 * delta
        self.start_time = start_time

        self.tx_id_lock = threading.Lock()
        self.global_tx_id = 0
        self.pending_transactions = {}
        self.vote_counts = {}
        self.voted_senders = {}
        self.notarized_tx_ids = set()
        self.port = port
        self.ports = ports
        print(f"Initialized Node {self.node_id} on port {self.port}")
        self.running = True
        self.lock = threading.Lock()
        self.current_epoch = 1
        self.blockchain = []  # Local chain of finalized blocks
        self.notarized_blocks = {}
        self.seed = None  # Store the seed here

        # Initialize notarized_blocks as a dictionary
        self.notarized_blocks = {}

        # Create and add the genesis block to notarized_blocks
        self.genesis_block = Block(epoch=0, previous_hash=b'0' * 20, transactions={}, length=0)
        self.notarized_blocks[0] = self.genesis_block
        self.blockchain.append(self.genesis_block)

        # For echoing messages
        self.seen_messages = set()
        self.message_queue = Queue()

        # Confusion period parameters
        self.confusion_start = 2  # Adjust as needed
        self.confusion_duration = 2  # Adjust as needed

    def set_seed(self, seed):
        """Sets the seed."""
        self.seed = seed

    def get_leader(self, epoch):
        """
        Determines the leader for a given epoch, implementing confusion period logic.
        """
        if epoch < self.confusion_start or epoch >= self.confusion_start + self.confusion_duration - 1:
            random.seed(epoch + int(hashlib.sha1(self.seed.encode()).hexdigest(), 16))
            return random.randint(0, self.total_nodes - 1)
        else:
            return epoch % self.total_nodes

    def start_network_listener(self):
        listener_thread = threading.Thread(target=self.network_listener, daemon=True)
        listener_thread.start()

    def network_listener(self):
        """
        Initializes a listening socket on the node's port and handles incoming connections.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('localhost', self.port))
            sock.listen()
            print(f"Node {self.node_id} listening on port {self.port}")

            while True:
                conn, _ = sock.accept()
                threading.Thread(target=self.handle_connection, args=(conn,), daemon=True).start()

    def handle_connection(self, conn):
        with conn:
            try:
                data = conn.recv(4096)
                if not data:
                    return
                message = Message.deserialize(data)
                if message:
                    self.message_queue.put(message)
                else:
                    print(f"Node {self.node_id}: Failed to deserialize message.")
            except Exception as e:
                print(f"Node {self.node_id}: Error handling connection: {e}")

    def calculate_start_datetime(self, start_time):
        now = datetime.now()
        start_hour, start_minute = map(int, start_time.split(":"))
        start_datetime = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

        if start_datetime < now:
            start_datetime = now  # Start now

        return start_datetime

    def wait_for_start(self, start_datetime):
        now = datetime.now()
        wait_seconds = (start_datetime - now).total_seconds()
        if wait_seconds > 0:
            print(f"Waiting for {int(wait_seconds)} seconds until start time {start_datetime}.")
            time.sleep(wait_seconds)
        else:
            print(f"Start time {start_datetime} is now or has passed. Starting immediately.")

    def run(self):
        # Wait for the seed signal to start the protocol
        start_datetime = self.calculate_start_datetime(self.start_time)
        self.wait_for_start(start_datetime)

        if not self.seed:
            print(f"Node {self.node_id}: Seed not set. Exiting run method.")
            return

        for epoch in range(1, self.total_epochs + 1):
            self.current_epoch = epoch
            print(f"=== Epoch {epoch} ===")
            self.generate_transactions_for_epoch(epoch)

            leader_id = self.get_leader(epoch)
            if self.node_id == leader_id:
                self.propose_block(epoch)
            else:
                # Wait for a proposal from the leader
                proposal_received = False
                wait_time = 0
                while wait_time < self.epoch_duration:
                    time.sleep(1)
                    wait_time += 1
                    # Process messages
                    while not self.message_queue.empty():
                        msg = self.message_queue.get()
                        self.process_message(msg)
                        if msg.type == MessageType.PROPOSE and msg.content.epoch == epoch:
                            proposal_received = True
                    if proposal_received:
                        break
                if not proposal_received:
                    # Backup leader steps up
                    if self.node_id == (leader_id + 1) % self.total_nodes:
                        print(f"Node {self.node_id}: No proposal received for epoch {epoch}. Acting as backup leader.")
                        self.propose_block(epoch)

            # Process remaining messages
            while not self.message_queue.empty():
                msg = self.message_queue.get()
                self.process_message(msg)

            time.sleep(max(0, self.epoch_duration - wait_time))
        self.display_blockchain()

    def propose_block(self, epoch):
        if epoch == 0:
            print("Genesis block is already set; skipping proposal for epoch 0.")
            return None

        # Retrieve the longest notarized chain
        longest_chain = self.get_longest_notarized_chain()
        previous_block = longest_chain[-1] if longest_chain else self.genesis_block
        previous_hash = previous_block.hash if previous_block else b'0' * 20
        length = previous_block.length + 1 if previous_block else 1

        with self.lock:
            block_transactions = self.pending_transactions.get(epoch, []).copy()
            new_block = Block(epoch, previous_hash, {tx.tx_id: tx for tx in block_transactions}, length)
            # Remove transactions from pending_transactions
            if epoch in self.pending_transactions:
                del self.pending_transactions[epoch]

        print(f"Node {self.node_id} proposes Block: {new_block.hash.hex()} with previous hash {previous_hash.hex()}, length {length}, and transactions {list(new_block.transactions.keys())}")

        # Create a Propose message and broadcast it
        propose_message = Message.create_propose_message(new_block, self.node_id)
        self.broadcast_message(propose_message)
        return new_block

    def vote_on_block(self, block):
        longest_notarized_chain = self.get_longest_notarized_chain()
        longest_notarized_length = longest_notarized_chain[-1].length if longest_notarized_chain else 0
        if block.length <= longest_notarized_length:
            print(f"Node {self.node_id}: Ignoring vote for Block {block.hash.hex()} in epoch {block.epoch} (length <= {longest_notarized_length})")
            return

        with self.lock:
            block_hash = block.hash.hex()

            if block_hash not in self.vote_counts:
                self.vote_counts[block_hash] = 0

            if block_hash not in self.voted_senders:
                self.voted_senders[block_hash] = set()

            if self.node_id not in self.voted_senders[block_hash]:
                self.vote_counts[block_hash] += 1
                self.voted_senders[block_hash].add(self.node_id)
                print(f"Node {self.node_id} voted for Block {block_hash} in epoch {block.epoch}")
            else:
                print(f"Node {self.node_id} already voted for Block {block_hash} in epoch {block.epoch}")
                return

        # Broadcast vote to all nodes
        vote_message = Message.create_vote_message(block, self.node_id)
        self.broadcast_message(vote_message)

        # Check if the block should be notarized
        self.notarize_block(block)

    def notarize_block(self, block):
        with self.lock:
            block_hash = block.hash.hex()

            # Check if this block is already notarized
            if block.epoch in self.notarized_blocks and self.notarized_blocks[block.epoch].hash == block.hash:
                print(f"Block {block_hash} has already been notarized in epoch {block.epoch}")
                return

            # Check if vote count meets quorum
            if self.vote_counts.get(block_hash, 0) > self.total_nodes // 2:
                self.notarized_blocks[block.epoch] = block
                print(f"Node {self.node_id}: Block {block_hash} notarized in epoch {block.epoch} with transactions {list(block.transactions.keys())}")

                for tx_id in block.transactions.keys():
                    self.notarized_tx_ids.add(tx_id)

                self.finalize_blocks()

    def finalize_blocks(self):
        # Build the chain of notarized blocks starting from the longest chain
        chain = self.get_longest_notarized_chain()
        # The chain is ordered from genesis to latest
        for i in range(len(chain) - 2):
            block_a = chain[i]
            block_b = chain[i + 1]
            block_c = chain[i + 2]
            # Check for three consecutive notarized blocks with consecutive epoch numbers
            if (block_b.epoch == block_a.epoch + 1) and (block_c.epoch == block_b.epoch + 1):
                # Finalize block_b and its parent chain if not already finalized
                if block_b not in self.blockchain:
                    print(f"Node {self.node_id}: Finalizing Block {block_b.hash.hex()} in epoch {block_b.epoch}")
                    # Add the parent chain up to block_b
                    for block in chain[:i+2]:
                        if block not in self.blockchain:
                            self.blockchain.append(block)

    def get_longest_notarized_chain(self):
        with self.lock:
            if not self.notarized_blocks:
                return []
            # Build the chain starting from the block with the highest length
            blocks_by_length = sorted(self.notarized_blocks.values(), key=lambda b: b.length, reverse=True)
            longest_chain = []
            for block in blocks_by_length:
                chain = []
                current_block = block
                while current_block:
                    chain.insert(0, current_block)
                    current_block = self.notarized_blocks.get(current_block.epoch - 1)
                if len(chain) >= len(longest_chain):
                    longest_chain = chain
            return longest_chain

    def add_transaction(self, transaction, epoch):
        with self.lock:
            next_epoch = epoch + 1

            # Ensure the next epoch entry is initialized if it doesn't exist
            if next_epoch not in self.pending_transactions:
                self.pending_transactions[next_epoch] = []

            # Check if the transaction already exists in the blockchain or is notarized
            for block in self.blockchain:
                if transaction.tx_id in block.transactions:
                    return

            if transaction.tx_id in self.notarized_tx_ids:
                return

            # Avoid adding the transaction if it's already in the pending list
            for txs in self.pending_transactions.values():
                if any(tx.tx_id == transaction.tx_id for tx in txs):
                    return

            # Add the transaction to the pending list for the next epoch
            self.pending_transactions[next_epoch].append(transaction)

    def get_next_tx_id(self):
        with self.tx_id_lock:
            self.global_tx_id += 1
            return self.global_tx_id

    def generate_random_transaction_for_epoch(self, epoch):
        sender = f"Client{random.randint(1, 100)}"
        receiver = f"Client{random.randint(1, 100)}"
        amount = random.randint(1, 1000)

        # Generate a unique transaction ID
        tx_id = self.get_next_tx_id()
        transaction = Transaction(tx_id, sender, receiver, amount)

        # Send transaction to self
        self.add_transaction(transaction, self.current_epoch)

    def generate_transactions_for_epoch(self, epoch):
        num_transactions = random.randint(1, 3)  # Random number of transactions per epoch
        for _ in range(num_transactions):
            self.generate_random_transaction_for_epoch(epoch)

    def broadcast_message(self, message):
        serialized_message = message.serialize()
        for target_port in self.ports:
            if target_port != self.port:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect(('localhost', target_port))
                        s.sendall(serialized_message)
                except Exception as e:
                    pass  # Ignore exceptions for simplicity

    def process_message(self, message):
        # Compute a unique identifier for the message
        message_hash = hashlib.sha1(message.serialize()).hexdigest()
        if message_hash in self.seen_messages:
            return  # Already processed this message
        else:
            self.seen_messages.add(message_hash)
            # If this is not an ECHO message, echo it
            if message.type != MessageType.ECHO:
                echo_message = Message.create_echo_message(message, self.node_id)
                self.broadcast_message(echo_message)

        # Process the message content
        if message.type == MessageType.PROPOSE:
            block = message.content
            self.vote_on_block(block)
        elif message.type == MessageType.VOTE:
            block = message.content
            block_hash = block.hash.hex()
            sender_id = message.sender
            with self.lock:
                if block_hash not in self.vote_counts:
                    self.vote_counts[block_hash] = 0
                if block_hash not in self.voted_senders:
                    self.voted_senders[block_hash] = set()
                if sender_id not in self.voted_senders[block_hash]:
                    self.vote_counts[block_hash] += 1
                    self.voted_senders[block_hash].add(sender_id)
                    self.notarize_block(block)
        elif message.type == MessageType.ECHO:
            # Process the echoed message
            original_message = message.content
            self.process_message(original_message)

    def display_blockchain(self):
        if not self.blockchain:
            print(f"Node {self.node_id}: Blockchain is empty.")
            return

        print(f"Node {self.node_id}: Current Blockchain:")
        for index, block in enumerate(self.blockchain):
            print(f"Block {index}:")
            print(f"  Hash: {block.hash.hex()}")
            print(f"  Previous Hash: {block.previous_hash.hex()}")
            print(f"  Epoch: {block.epoch}")
            print(f"  Length: {block.length}")
            print(f"  Transactions: {len(block.transactions)} transactions")

            for tx_id, tx in block.transactions.items():
                print(f"    Transaction {tx_id}: from {tx.sender} to {tx.receiver} of {tx.amount} coins")
            print("-" * 40)
