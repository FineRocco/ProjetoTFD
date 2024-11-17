from datetime import datetime, timedelta
import threading
import socket
import time
import random
import sys

from block import Block
from message import Message, MessageType
from transaction import Transaction

class Node(threading.Thread):
    """
    Represents a blockchain node in a network running the Streamlet consensus protocol.
    Each node can propose, vote, and notarize blocks, and broadcasts messages to other nodes.
    """
    def __init__(self, node_id, total_nodes, total_epochs, delta, port, ports, start_time):
        super().__init__()
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.total_epochs = total_epochs
        self.epoch_duration = 2 * delta
        self.start_time = start_time

        self.tx_id_lock = threading.Lock()  # Lock to synchronize transaction ID generation
        self.global_tx_id = 0  # Global transaction counter
        self.pending_transactions = {}  
        self.vote_counts = {}  
        self.voted_senders = {} 
        self.notarized_tx_ids = set() 
        self.port = port
        self.ports = ports  
        print(f"Initialized Node {self.node_id} on port {self.port}") 
        self.lock = threading.Lock()
        self.current_epoch = 1  
        self.blockchain = []  # Local chain of notarized blocks
        self.notarized_blocks = {}
        self.seed = None  # Store the seed here
        self.running = False  # Flag to control the main loop

        # Initialize notarized_blocks as a dictionary
        self.notarized_blocks = {}
        
        # Create and add the genesis block to notarized_blocks
        self.genesis_block = Block(epoch=0, previous_hash=b'0' * 20, transactions={})
        self.notarized_blocks[0] = self.genesis_block
        self.blockchain.append(self.genesis_block)

    def initialize_sockets(self):
        """
        Initialize persistent outgoing sockets for all nodes.
        """
        self.sockets = {}
        # print(f"Node {self.node_id}: Initializing sockets. Current ports: {self.ports}")

        # Connect to other nodes
        for i, port in enumerate(self.ports):
            if i == self.node_id:
                continue  # Skip self connection

            retries = 3
            while retries > 0:
                try:
                    sock = socket.create_connection(('localhost', port), timeout=1)
                    self.sockets[i] = sock
                    print(f"Node {self.node_id}: Connected to Node {i} on port {port}. Socket: {sock}")
                    # print(f"Node {self.node_id}: Sockets after connection: {self.sockets}")
                    # print(f"Inside init, Node {self.node_id}: Socket for Node {i} has fileno: {sock.fileno()}")
                    break  # Exit the retry loop on success
                except (socket.timeout, ConnectionRefusedError):
                    retries -= 1
                    print(f"Node {self.node_id}: Failed to connect to Node {i} on port {port}. Retrying... ({3 - retries}/3)")
                    time.sleep(1)  # Wait before retrying

            if retries == 0:
                print(f"Node {self.node_id}: Could not connect to Node {i} on port {port} after 3 attempts.")


        print(f"Node {self.node_id}: Final state of sockets after initialization: {self.sockets}")

    def broadcast_message(self, message):
        """
        Broadcast a serialized message to all connected nodes using persistent sockets.
        """
        serialized_message = message.serialize()
        # print(f"Node {self.node_id}: Starting broadcast. Current sockets: {self.sockets}")

        for target_node_id, sock in self.sockets.items():
            try:
                # print(f"Inside boradcat, Node {self.node_id}: Socket has fileno: {sock.fileno()}")
                # print(f"Node {self.node_id}: Broadcasting to Node {target_node_id} using socket {sock}.")
                print(f"Inicial state of broadcast.{self.sockets}")
                sock.sendall(serialized_message)
                print(f"Node {self.node_id}: Successfully broadcasted to Node {target_node_id}.")
            except (socket.error, ConnectionResetError):
                print(f"Node {self.node_id}: Failed to send message to Node {target_node_id}.")
            except Exception as e:
                print(f"Node {self.node_id}: Error while broadcasting to Node {target_node_id}: {e}")

        print(f"Node {self.node_id}: Broadcast completed.")


    def handle_incoming_messages(self, listening_socket):
        """
        Listen for and process incoming messages using the provided listening socket.
        """
        try:
            print(f"Node {self.node_id}: Listening for incoming messages...")
            while self.running:
                try:
                    conn, addr = listening_socket.accept()
                    print(f"Node {self.node_id}: Accepted connection from {addr}")
                    with conn:
                        blockchain_tx_ids = {tx_id for block in self.blockchain for tx_id in block.transactions.keys()}
                        notarized_tx_ids = self.notarized_tx_ids

                        message = Message.deserialize_from_socket(conn, blockchain_tx_ids, notarized_tx_ids)
                        if message is None:
                            print(f"Node {self.node_id}: Deserialization failed. Ignoring message.")
                            continue

                        print(f"Node {self.node_id}: Received message of type {message.type}")

                        # Process the message
                        self.process_message(message)
                except Exception as e:
                    print(f"Node {self.node_id}: Error in message handling - {e}")

        except Exception as e:
            print(f"Node {self.node_id}: Error in message handling - {e}")

    def process_message(self, message):
        # Handle various message types
        if message.type == MessageType.PROPOSE:
            # Vote on the received proposed block
            block = message.content
            self.vote_on_block(block)
            print(f"Node {self.node_id} voted for block {block.hash.hex()}.")

        elif message.type == MessageType.VOTE:
            # Handle a vote on a block and update notarization if conditions are met
            block = message.content
            block_hash = block.hash.hex()
            sender_id = message.sender  # Ensure the message includes sender ID

            print(f"Node {self.node_id}: Received Vote from Node {sender_id} for Block {block_hash} in epoch {block.epoch}")

            # Initialize vote tracking structures
            if block_hash not in self.vote_counts:
                self.vote_counts[block_hash] = 0
            if block_hash not in self.voted_senders:
                self.voted_senders[block_hash] = set()

            # Check if this sender has already voted for this block
            if sender_id not in self.voted_senders[block_hash]:
                # Add vote and update vote counts
                self.vote_counts[block_hash] += 1
                self.voted_senders[block_hash].add(sender_id)
                print(f"Node {self.node_id}: Updated vote count for Block {block_hash} to {self.vote_counts[block_hash]}")
            else:
                print(f"Node {self.node_id}: Duplicate vote from Node {sender_id} for Block {block_hash}; ignoring.")

            # Check notarization condition
            self.notarize_block(block)
            print(f"Node {self.node_id}: Checking notarization for Block {block_hash} with updated votes = {self.vote_counts.get(block_hash, 0)}")

        elif message.type == MessageType.ECHO_NOTARIZE:
            # Update the node’s view of notarized blocks based on an echo message
            block = message.content
            if block.epoch not in self.notarized_blocks or self.notarized_blocks[block.epoch].hash != block.hash:
                self.notarized_blocks[block.epoch] = block
                # Adicionar tx_id das transações notarizadas via Echo
                for tx_id in block.transactions.keys():
                    self.notarized_tx_ids.add(tx_id)
                    #print(f"Node {node_id}: Transaction {tx_id} added to notarized_tx_ids via Echo.")
                #print(f"Node {node_id}: Updated notarization from Echo for Block {block.hash.hex()} in epoch {block.epoch}")
                self.finalize_blocks()  # Re-check finalization criteria

        elif message.type == MessageType.ECHO_TRANSACTION:
            # Add echoed transaction to pending transactions if it’s new
            content = message.content
            transaction = content['transaction']
            epoch = content['epoch']
            #print(f"Echoed Transaction ID: {transaction.tx_id}, Sender: {transaction.sender}, Receiver: {transaction.receiver}, Amount: {transaction.amount}, Epoch: {epoch}")
            self.add_transaction(transaction, epoch)
            #print(f"Node {node_id} added echoed transaction {transaction.tx_id} to pending transactions for epoch {epoch}.")

        elif message.type == MessageType.DISPLAY_BLOCKCHAIN:
            self.display_blockchain()

    def calculate_start_datetime(self, start_time):
        """Calculate the start datetime from a 24-hour time string."""
        now = datetime.now()
        start_hour, start_minute = map(int, start_time.split(":"))
        start_datetime = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        # If the start time is in the past, schedule it for the next day
        if start_datetime < now:
            start_datetime += timedelta(days=1)
        
        return start_datetime

    def wait_for_start(self, start_datetime):
        """Wait until the specified start datetime."""
        now = datetime.now()
        wait_seconds = (start_datetime - now).total_seconds()
        if wait_seconds > 0:
            print(f"Waiting for {int(wait_seconds)} seconds until start time {start_datetime}.")
            time.sleep(wait_seconds)
        else:
            print(f"Start time {start_datetime} is now or has passed. Starting immediately.")

    def next_leader(self, seed):
        random.seed(seed)
        current_leader = random.randint(0, self.total_nodes - 1)
        #TDOD Check if chosen leader is alive, if not choose another one.
        if (current_leader == self.node_id):
            self.propose_block(self.current_epoch)

    def set_seed(self, seed, sock):
        """Sets the seed and starts the consensus protocol."""
        print(f"Socket fileno: {sock.fileno()} (should be >= 0 if open)")
        self.seed = seed

    def run(self):
        """
        Main loop for the consensus protocol.
        """
        print(f"Node {self.node_id}: Waiting for the time to start.")

        # Wait for the seed signal to start the protocol
        start_datetime = self.calculate_start_datetime(self.start_time)
        self.wait_for_start(start_datetime)
    
        if not self.seed:
            print(f"Node {self.node_id}: Seed not set. Exiting run method.")
            return
        
        for epoch in range(1, self.total_epochs + 1):
            self.current_epoch=epoch
            print(f"=== Epoch {epoch} ===")
            self.next_leader(self.seed)
            self.generate_transactions_for_epoch(epoch)
            time.sleep(self.epoch_duration)
            
        self.display_blockchain()

    def propose_block(self, epoch):
        """
        Proposes a new block at the start of an epoch if the node is the leader.
        """
        if epoch == 0:
            print("Genesis block is already set; skipping proposal for epoch 0.")
            return None

        # Retrieve the latest block in the notarized chain
        previous_block = self.get_longest_notarized_chain()
        previous_hash = previous_block.hash if previous_block else b'1' * 20

        with self.lock:
            block_transactions = self.pending_transactions.get(epoch, []).copy()
            new_block = Block(epoch, previous_hash, {tx.tx_id: tx for tx in block_transactions})
            
            if epoch in self.pending_transactions:
                del self.pending_transactions[epoch]
                print(f"Node {self.node_id}: Cleared pending_transactions for epoch {epoch} after proposing the block.")

        print(f"Node {self.node_id} proposes Block: {new_block.hash.hex()} with previous hash {previous_hash.hex()} and transactions {list(new_block.transactions.keys())}")

        # Create a Propose message and broadcast it
        propose_message = Message.create_propose_message(new_block, self.node_id)
        self.broadcast_message(propose_message)
        return new_block

    def vote_on_block(self, block):
        """
        Votes on a proposed block if it extends the longest notarized chain.

        :param block: Block - The proposed block.
        """
        print(f"Node {self.node_id}: Preparing to vote on Block {block.hash.hex()} with transactions: {list(block.transactions.keys())}")
        longest_notarized_block = self.get_longest_notarized_chain()
        if longest_notarized_block and block.epoch <= longest_notarized_block.epoch:
            print(f"Node {self.node_id}: Ignorando votação para Block {block.hash.hex()} em epoch {block.epoch} (epoch <= {longest_notarized_block.epoch})")
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
                print(f"Node {self.node_id} já votou para Block {block_hash} em epoch {block.epoch}")
                return

        # Broadcast vote to all nodes
        vote_message = Message.create_vote_message(block, self.node_id)
        self.broadcast_message(vote_message)

        # Check if the block should be notarized
        self.notarize_block(block)

    def notarize_block(self, block):
        """
        Notarizes a block if it receives more than n/2 votes, and notifies other nodes.

        :param block: Block - The block to notarize.
        """
        with self.lock:
            block_hash = block.hash.hex()
            print(f"Node {self.node_id}: Checking notarization for Block {block_hash} with votes = {self.vote_counts.get(block_hash, 0)}")

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
                    #print(f"Node {self.node_id}: Transaction {tx_id} added to notarized_tx_ids.")

                # Broadcast notarization to all nodes
                echo_message = Message.create_echo_notarize_message(block, self.node_id)
                self.broadcast_message(echo_message)
                self.finalize_blocks()

    def finalize_blocks(self):
        print(f"Node {self.node_id}: Checking for finalization. Current blockchain: {[(b.epoch, list(b.transactions.keys())) for b in self.blockchain]}")
        notarized_epochs = sorted(self.notarized_blocks.keys())
        print(f"Node {self.node_id}: Notarized epochs: {notarized_epochs}")
        
        for i in range(2, len(notarized_epochs)):
            # Check for three consecutive epochs
            if (notarized_epochs[i] == notarized_epochs[i - 1] + 1 and
                notarized_epochs[i - 1] == notarized_epochs[i - 2] + 1):
                
                # Finalize the second block in this sequence of three consecutive epochs
                second_epoch = notarized_epochs[i - 1]
                finalized_block = self.notarized_blocks[second_epoch]
                
                # Ensure the block and its chain are not already in the blockchain
                if finalized_block not in self.blockchain:
                    print(f"Node {self.node_id}: Finalizing Block {finalized_block.hash.hex()} in epoch {finalized_block.epoch}")
                    
                    # Add the finalized block and its entire parent chain to the blockchain
                    chain = self.get_chain_to_block(finalized_block)
                    
                    # Print details of each block in the chain for debugging
                    print(f"Node {self.node_id}: Finalized chain to add:")
                    for b in chain:
                        print(f"  Block {b.epoch}: Hash {b.hash.hex()}, Previous Hash {b.previous_hash.hex()}, Transactions: {list(b.transactions.keys())}")

                    self.blockchain.extend(chain)
                    print(f"Node {self.node_id}: Extended blockchain with chain ending in epoch {second_epoch}")
        
    def get_chain_to_block(self, block):
        chain = []
        current_block = block
        while current_block and current_block not in self.blockchain:
            print(f"Node {self.node_id}: Adding Block {current_block.epoch} to chain with hash {current_block.hash.hex()}")
            chain.insert(0, current_block)
            current_block = next(
                (b for b in self.notarized_blocks.values() if b.hash == current_block.previous_hash), None
            )
            if current_block:
                print(f"Node {self.node_id}: Moving to previous block with epoch {current_block.epoch} and hash {current_block.hash.hex()}")
            else:
                print(f"Node {self.node_id}: Reached end of chain or genesis block.")
        return chain


    def get_longest_notarized_chain(self):
        with self.lock:
            if not self.notarized_blocks:
                return None  
            latest_epoch = max(self.notarized_blocks.keys())
            return self.notarized_blocks[latest_epoch]

    def add_transaction(self, transaction, epoch):
        with self.lock:
            next_epoch = epoch + 1
            #print(f"Node {self.node_id}: Adding transaction {transaction.tx_id} to pending transactions for epoch {next_epoch}")
            #print(f"Node {self.node_id}: Current pending transactions before add: {self.pending_transactions}")

            # Ensure the next epoch entry is initialized if it doesn't exist
            if next_epoch not in self.pending_transactions:
                self.pending_transactions[next_epoch] = []

            # Check if the transaction already exists in the blockchain or is notarized
            for block in self.blockchain:
                if transaction.tx_id in block.transactions:
                    #print(f"Node {self.node_id}: Transaction {transaction.tx_id} already included in blockchain. Ignoring.")
                    return

            if transaction.tx_id in self.notarized_tx_ids:
                #print(f"Node {self.node_id}: Transaction {transaction.tx_id} already notarized. Ignoring.")
                return

            # Avoid adding the transaction if it's already in the pending list
            for txs in self.pending_transactions.values():
                if any(tx.tx_id == transaction.tx_id for tx in txs):
                    #print(f"Node {self.node_id}: Transaction {transaction.tx_id} already exists in pending transactions. Ignoring.")
                    return

            # Add the transaction to the pending list for the next epoch
            self.pending_transactions[next_epoch].append(transaction)
            #print(f"Node {self.node_id} added transaction {transaction.tx_id} to pending transactions for epoch {next_epoch}.")

    def get_next_tx_id(self):
        """
        Generates a globally unique transaction ID.

        :return: int - The next available transaction ID.
        """
        with self.tx_id_lock:
            self.global_tx_id += 1
            return self.global_tx_id

    def generate_random_transaction_for_epoch(self, epoch):
        """
        Creates a random transaction and sends it to a randomly selected node in the network for a specific epoch.

        :param epoch: int - The epoch to which the transaction belongs.
        """
        sender = f"Client{random.randint(1, 100)}"
        receiver = f"Client{random.randint(1, 100)}"
        amount = random.randint(1, 1000)

        # Generate a unique transaction ID
        tx_id = self.get_next_tx_id()
        transaction = Transaction(tx_id, sender, receiver, amount)

        # Send transaction to a random node
        target_id = random.randint(0, self.total_nodes-1)
        if target_id == self.node_id:
            self.add_transaction(transaction, self.current_epoch)
            echo_message = Message.create_echo_transaction_message(transaction, epoch, self.node_id)
            self.broadcast_message(echo_message)

    def generate_transactions_for_epoch(self, epoch):
        """
        Generates a random number of transactions for a specific epoch.

        :param epoch: int - The epoch for which transactions are to be generated.
        """
        num_transactions = random.randint(1, 3)  # Random number of transactions per epoch
        for _ in range(num_transactions):
            self.generate_random_transaction_for_epoch(epoch)

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
            print(f"  Transactions: {len(block.transactions)} transactions")
            
            for tx_id, tx in block.transactions.items():  # Unpack tx_id and Transaction object
                print(f"    Transaction {tx_id}: from {tx.sender} to {tx.receiver} of {tx.amount} coins")
            print("-" * 40)  # Separator for each block
