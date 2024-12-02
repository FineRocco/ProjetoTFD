from datetime import datetime
import json
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
    def __init__(self, node_id, total_nodes, total_epochs, delta, port, ports, start_time, rejoin):
        super().__init__()
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.total_epochs = total_epochs
        self.epoch_duration = 2 * delta
        self.start_time = start_time
        self.recovery_completed = False  # Flag to indicate recovery completion
        self.rejoin = rejoin # Flag to indicate a rejoin

        self.current_leader = -1  # ID of the current leader
        self.tx_id_lock = threading.Lock()  # Lock to synchronize transaction ID generation
        self.global_tx_id = 0  # Global transaction counter
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
        self.blockchain = []  # Local chain of notarized blocks
        self.notarized_blocks = {}
        self.seed = None  # Store the seed here
        self.running = False  # Flag to control the main loop

        # Initialize notarized_blocks as a dictionary
        self.notarized_blocks = {}

        self.genesis_block = Block(epoch=0, previous_hash=b'0' * 20, transactions={})

    def get_next_leader(self, seed):
        """Gets the next leader based on the provided seed."""
        epoch_seed = f"{seed}-{self.current_epoch}"
        random.seed(epoch_seed)  # Use a combined seed for variability
        return random.randint(0, self.total_nodes - 1)

    def next_leader(self, seed):
        self.current_leader = self.get_next_leader(seed)
        print(f"Node {self.node_id}: Leader for epoch {self.current_epoch} is Node {self.current_leader}")
        if (self.current_leader == self.node_id):
            self.propose_block(self.current_epoch)

    def set_seed(self, seed):
        """Sets the seed and starts the consensus protocol."""
        self.seed = seed
        self.running = True
        self.start()  # Start the thread, which calls run()

    def run(self):
        if not self.rejoin:
            # Wait to start the protocol
            start_datetime = self.calculate_start_datetime(self.start_time)
            self.wait_for_start(start_datetime)
        
        # Attempt to load the blockchain from a file
        self.load_blockchain()

        # Determine if the node is rejoining or starting fresh
        if self.rejoin:
            if self.blockchain:
                # Rejoining node recovers its state
                print(f"Node {self.node_id}: Detected existing blockchain. Recovering...")
                self.recover_blockchain()
            else:
                print(f"Node {self.node_id}: No blockchain found. Starting from genesis.")
                self.notarized_blocks[0] = self.genesis_block
                self.blockchain.append(self.genesis_block)
        else:
            # New node adds the genesis block
            if not self.blockchain:
                self.notarized_blocks[0] = self.genesis_block
                self.blockchain.append(self.genesis_block)

        # Determine current epoch based on the saved blockchain
        last_saved_epoch = max(block.epoch for block in self.blockchain) if self.blockchain else 0
        self.current_epoch = last_saved_epoch + 1
        
        for epoch in range(self.current_epoch, self.total_epochs + 1):
            self.current_epoch = epoch
            print(f"==================================== Epoch {epoch} ====================================")
            self.next_leader(self.seed)
            threading.Thread(target=self.generate_transactions_for_epoch,args=(epoch,),daemon=True).start()

            time.sleep(self.epoch_duration)

            # Save the blockchain after the epoch
            self.save_blockchain()

        self.display_blockchain()

    def calculate_start_datetime(self, start_time):
        """
        Calculate the start datetime based on the provided start_time string in HH:MM format.
        """
        now = datetime.now()
        start_hour, start_minute = map(int, start_time.split(":"))
        start_datetime = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        # If the start time is in the past, do not wait and start immediately
        if start_datetime < now:
            start_datetime = now  # Start now
        
        return start_datetime

    def wait_for_start(self, start_datetime):
        """
        Wait until the specified start_datetime.
        """
        now = datetime.now()
        wait_seconds = (start_datetime - now).total_seconds()
        if wait_seconds > 0:
            print(f"Waiting for {int(wait_seconds)} seconds until start time {start_datetime}.")
            time.sleep(wait_seconds)
        else:
            print(f"Start time {start_datetime} is now or has passed. Starting immediately.")

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
        self.vote_on_block(new_block)

        # Create a Propose message and broadcast it
        propose_message = Message.create_propose_message(new_block, self.node_id)
        threading.Thread(target=self.broadcast_message,args=(propose_message,),daemon=True).start()

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
        threading.Thread(target=self.broadcast_message,args=(vote_message,),daemon=True).start()

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
            threading.Thread(
            target=self.broadcast_message,
            args=(echo_message,),
            daemon=True  # Daemon threads will exit when the main program exits
            ).start()

    def generate_transactions_for_epoch(self, epoch):
        """
        Generates a random number of transactions for a specific epoch.

        :param epoch: int - The epoch for which transactions are to be generated.
        """
        num_transactions = random.randint(1, 3)  # Random number of transactions per epoch
        for _ in range(num_transactions):
            self.generate_random_transaction_for_epoch(epoch)

    def broadcast_message(self, message):
        serialized_message = message.serialize()
        for target_port in self.ports:
            if target_port != self.port:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        print(f"Node {self.node_id} broadcasting to port {target_port}")
                        s.connect(('localhost', target_port))
                        s.sendall(serialized_message)
                        print(f"Node {self.node_id} successfully broadcasted to port {target_port}")
                except ConnectionRefusedError:
                    print(f"Node {self.node_id} could not connect to Node at port {target_port}")
                except Exception as e:
                    print(f"Node {self.node_id} encountered an error while broadcasting to port {target_port}: {e}")

    def send_message_to_port(self, target_port, message):
        """
        Sends a message to a specific port.

        Parameters:
        - target_port (int): The port of the target node.
        - message (Message): The message to send.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', target_port))
                s.sendall(message.serialize())
                print(f"Node {self.node_id}: Sent {message.type} to port {target_port}")
        except Exception as e:
            print(f"Node {self.node_id}: Error sending {message.type} to port {target_port}: {e}")

    def save_blockchain(self):
        """Saves the blockchain to a file without using list comprehensions."""
        file_name = f"blockchain_{self.node_id}.json"
        blockchain_data = []  # Initialize an empty list to hold the serialized blocks

        # Process each block in the blockchain
        for block in self.blockchain:
            # Serialize block data
            serialized_block = {
                "epoch": block.epoch,
                "previous_hash": block.previous_hash.hex(),
                "transactions": [],  # Initialize an empty list for transactions
                "hash": block.hash.hex()
            }

            # Process each transaction in the block
            for tx_id, tx in block.transactions.items():
                serialized_transaction = {
                    "tx_id": tx_id,
                    "sender": tx.sender,
                    "receiver": tx.receiver,
                    "amount": tx.amount
                }
                # Add the serialized transaction to the block's transactions list
                serialized_block["transactions"].append(serialized_transaction)

            # Add the serialized block to the blockchain data
            blockchain_data.append(serialized_block)

        # Write the serialized blockchain data to a file
        try:
            with open(file_name, 'w') as f:
                json.dump(blockchain_data, f, indent=4)
            print(f"Node {self.node_id}: Blockchain saved to {file_name}")
        except Exception as e:
            print(f"Node {self.node_id}: Error saving blockchain to file: {e}")

    def load_blockchain(self):
        """Loads the blockchain from a file."""
        file_name = f"blockchain_{self.node_id}.json"
        try:
            with open(file_name, 'r') as f:
                blockchain_data = json.load(f)
            blockchain = []
            for block_data in blockchain_data:
                block = Block(
                    epoch=block_data["epoch"],
                    previous_hash=bytes.fromhex(block_data["previous_hash"]),
                    transactions={
                        tx["tx_id"]: Transaction(
                            tx_id=tx["tx_id"], sender=tx["sender"], receiver=tx["receiver"], amount=tx["amount"]
                        )
                        for tx in block_data["transactions"]
                    }
                )
                blockchain.append(block)
            self.blockchain = blockchain
            self.notarized_blocks = {block.epoch: block for block in self.blockchain}
            print(f"Node {self.node_id}: Blockchain loaded from {file_name}")
        except FileNotFoundError:
            print(f"Node {self.node_id}: No saved blockchain file found.")
        except Exception as e:
            print(f"Node {self.node_id}: Error loading blockchain from file: {e}")

    def recover_blockchain(self):
        """
        Recover the blockchain for a rejoining node.
        """
        print(f"Node {self.node_id}: Starting blockchain recovery...")

        # Load blockchain from file
        self.load_blockchain()

        # Determine the last saved epoch
        last_saved_epoch = max(block.epoch for block in self.blockchain) if self.blockchain else 0
        print(f"Node {self.node_id}: Last saved epoch: {last_saved_epoch}")

        # Broadcast QUERY_MISSING_BLOCKS with the last saved epoch
        query_message = Message(MessageType.QUERY_MISSING_BLOCKS, {"last_epoch": last_saved_epoch}, self.port)
        self.broadcast_message(query_message)

        # Wait for missing blocks to be recovered
        start_time = time.time()
        while not self.recovery_completed:
            if time.time() - start_time > 15:  # Timeout after 15 seconds
                print(f"Node {self.node_id}: Recovery timeout. Proceeding with partial blockchain.")
                break
            time.sleep(0.1)

        # Ensure the current epoch is updated after recovery
        self.current_epoch = max(block.epoch for block in self.blockchain) + 1 if self.blockchain else 1
        print(f"Node {self.node_id}: Blockchain recovery complete. Current epoch: {self.current_epoch}")

    def display_blockchain(self):
        if not self.blockchain:
            print(f"Node {self.node_id}: Blockchain is empty.")
            return

        print(f"Node {self.node_id}: Current Blockchain:")
        for block in self.blockchain:  # Directly iterate over blocks
            print(f"Block (Epoch {block.epoch}):")
            print(f"  Hash: {block.hash.hex()}")
            print(f"  Previous Hash: {block.previous_hash.hex()}")
            print(f"  Transactions: {len(block.transactions)} transactions")
            
            for tx_id, tx in block.transactions.items():  # Unpack tx_id and Transaction object
                print(f"    Transaction {tx_id}: from {tx.sender} to {tx.receiver} of {tx.amount} coins")
            print("-" * 40)  # Separator for each block

