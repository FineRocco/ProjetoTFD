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
    def __init__(self, node_id, total_nodes, total_epochs, delta, port, ports, start_time, rejoin, confusion_start=None, confusion_duration=None):
        super().__init__()
        # Node and network configuration
        self.node_id = node_id  # Unique identifier for the node
        self.total_nodes = total_nodes  # Total number of nodes in the network
        self.total_epochs = total_epochs  # Total number of epochs to run the protocol
        self.epoch_duration = 2 * delta  # Duration of each epoch based on the delta parameter
        self.start_time = start_time  # Start time for the protocol
        self.rejoin = rejoin  # Indicates whether the node is rejoining the network
        self.pending_proposes= {}
        self.confusion_notarized = False  # Indicates if confusion blocks have been resolved
        
        # Leader and consensus-related properties
        self.current_leader = -1  # ID of the current leader for the epoch
        self.current_epoch = 1  # Current epoch number

        # Synchronization and locks
        self.tx_id_lock = threading.Lock()  # Lock for thread-safe transaction ID generation
        self.lock = threading.Lock()  # General-purpose lock for thread-safe operations
        self.message_queue_lock = threading.Lock()  # Lock for managing the message queue
        self.pending_votes_lock = threading.Lock()  # Lock for managing the message queue
        self.pending_proposes_lock = threading.Lock()  # Lock for managing the message queue

        # Transaction and voting data
        self.global_tx_id = 0  # Counter for transaction IDs
        self.pending_transactions = {}  # Pending transactions for the current epoch
        self.vote_counts = {}  # Count of votes for each block
        self.voted_senders = {}  # Tracks nodes that have already voted
        self.notarized_tx_ids = set()  # IDs of transactions that have been notarized

        # Networking
        self.port = port  # Port this node listens on
        self.ports = ports  # List of all node ports in the network

        # Blockchain-related properties
        self.blockchain = []  # Local copy of the blockchain
        self.notarized_blocks = {}  # Dictionary of notarized blocks
        self.genesis_block = Block(epoch=0, previous_hash=b'0' * 20, transactions={})  # The genesis block

        # Protocol state
        self.seed = None  # Seed for deterministic leader selection
        self.running = False  # Indicates whether the main protocol loop is running
        self.recovery_completed = False  # Indicates whether recovery is complete

        # Confusion (fault-tolerance testing) configuration
        self.confusion_start = confusion_start if confusion_start is not None else -1  # Start of confusion period
        self.confusion_duration = confusion_duration if confusion_duration is not None else 0  # Duration of confusion period

        # Message handling
        self.message_queue = []  # Queue for incoming messages

        print(f"Initialized Node {self.node_id} on port {self.port}")

    def get_next_leader(self, seed):
        """Determines the leader for the current epoch using the provided seed."""
        epoch_seed = f"{seed}-{self.current_epoch}"  # Combine seed and epoch for variability
        random.seed(epoch_seed)  # Set the random seed
        return random.randint(0, self.total_nodes - 1)  # Select a random node as leader

    def next_leader(self, seed):
        """
        Determines the leader for the epoch based on the current epoch and confusion settings.
        Proposes a block if the node itself is selected as the leader.
        """
        confusion_end = self.confusion_start + self.confusion_duration - 1
        if self.current_epoch < self.confusion_start or self.current_epoch > confusion_end:
            # Normal operation: Use random leader selection
            self.current_leader = self.get_next_leader(seed)
        else:
            # Confusion period: Use deterministic leader selection
            self.current_leader = self.current_epoch % self.total_nodes

        print(f"Node {self.node_id}: Leader for epoch {self.current_epoch} is Node {self.current_leader}")

        # If the node is the leader, propose a block
        if self.current_leader == self.node_id:
            self.propose_block(self.current_epoch)

    def set_seed(self, seed):
        """Sets the seed for leader selection and starts the consensus protocol."""
        self.seed = seed
        self.running = True  # Enable the protocol loop
        self.start()  # Start the thread (calls `run`)

    def run(self):
        """Main loop for the node's consensus protocol."""
        if not self.rejoin:
            # Wait for the designated start time
            start_datetime = self.calculate_start_datetime(self.start_time)
            self.wait_for_start(start_datetime)

        # Load the blockchain from a file (if available)
        self.load_blockchain()

        if self.rejoin:
            # Rejoining node: Recover its previous state
            print(f"Node {self.node_id}: Recovering...")
            self.notarized_blocks[0] = self.genesis_block
            self.blockchain.append(self.genesis_block)
            self.recover_blockchain()
        else:
            # New node: Start with the genesis block
            if not self.blockchain:
                self.notarized_blocks[0] = self.genesis_block
                self.blockchain.append(self.genesis_block)

        # Calculate the starting epoch based on the blockchain state
        last_saved_epoch = max(block.epoch for block in self.blockchain) if self.blockchain else 0
        self.current_epoch = last_saved_epoch + 1


        for epoch in range(self.current_epoch, self.total_epochs + 1):
            self.current_epoch = epoch
            print(f"==================================== Epoch {epoch} ====================================")
        
            if epoch == self.confusion_start + self.confusion_duration:
                self.resolve_confusion()  # Resolve confusion when the period ends

            self.next_leader(self.seed)
            threading.Thread(target=self.generate_transactions_for_epoch, args=(epoch,), daemon=True).start()
            time.sleep(self.epoch_duration)

        # Display the final blockchain state
        self.display_blockchain()

    def calculate_start_datetime(self, start_time):
        """
        Calculate the start datetime based on the provided start_time string in HH:MM format.

        This function computes the datetime at which the protocol should start by
        combining the current date with the provided start time. If the calculated
        start time is earlier than the current time, the start is set to "now."
        """
        now = datetime.now()  # Get the current datetime
        start_hour, start_minute = map(int, start_time.split(":"))  # Extract hour and minute from the input string
        start_datetime = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)  # Set start time

        # If the start time has already passed, begin immediately
        if start_datetime < now:
            start_datetime = now
        
        return start_datetime

    def wait_for_start(self, start_datetime):
        """
        Wait until the specified start_datetime.

        This function pauses the node's execution until the start time is reached.
        If the start time has already passed, it starts immediately.
        """
        now = datetime.now()  # Get the current time
        wait_seconds = (start_datetime - now).total_seconds()  # Calculate the time to wait in seconds

        if wait_seconds > 0:
            print(f"Waiting for {int(wait_seconds)} seconds until start time {start_datetime}.")
            time.sleep(wait_seconds)  # Pause execution until the start time
        else:
            print(f"Start time {start_datetime} is now or has passed. Starting immediately.")
        
    def propose_block(self, epoch):
        """
        Proposes a block for the current epoch. During confusion, uses the correct parent block.
        """
        if epoch == 0:
            print("Genesis block is already set; skipping proposal for epoch 0.")
            return None

        confusion_end = self.confusion_start + self.confusion_duration - 1
        previous_block = None

        if epoch <= confusion_end:
            if epoch in self.notarized_blocks:
                previous_block = self.notarized_blocks[epoch - 1]
            else:
                previous_block = self.genesis_block
            print(f"Node {self.node_id}: Using {previous_block.hash.hex()} as parent during confusion.")
        else:
            previous_block = self.get_longest_notarized_chain()
            print(f"Node {self.node_id}: Resolving confusion, choosing Block {previous_block.hash.hex()} as parent.")

        previous_hash = previous_block.hash if previous_block else self.genesis_block.hash

        # Create the block
        with self.lock:
            block_transactions = self.pending_transactions.get(epoch, []).copy()
            new_block = Block(epoch, previous_hash, {tx.tx_id: tx for tx in block_transactions})

            if epoch in self.pending_transactions:
                del self.pending_transactions[epoch]

        print(f"Node {self.node_id} proposes Block: {new_block.hash.hex()} with previous hash {previous_hash.hex()} and transactions {list(new_block.transactions.keys())}")
        # If confusion is active, store the block in confusion_block
        self.vote_on_block(new_block)

        # Broadcast the proposal
        propose_message = Message.create_propose_message(new_block, self.node_id)
        threading.Thread(target=self.broadcast_message, args=(propose_message,), daemon=True).start()

    def resolve_confusion(self):
        if not self.confusion_notarized:
            print(f"Node {self.node_id}: Resolving confusion and notarizing blocks from confusion period.")
            for epoch, block in sorted(self.pending_proposes.items()):
                parent_block = self.notarized_blocks.get(block.epoch - 1, self.genesis_block)
                
                self.notarized_blocks[epoch] = block
                print(f"Node {self.node_id}: Notarized Block {block.hash.hex()} for epoch {epoch}.")
                broadcast_message = Message.create_propose_message(block, self.node_id)
                threading.Thread(target=self.broadcast_message, args=(broadcast_message,), daemon=True).start()
                threading.Thread(target=self.send_message_to_port, args=(self.port,broadcast_message), daemon=True).start()


    def synchronize_blockchain(self):
        """
        Synchronize the blockchain across all nodes to ensure consistency after the confusion period.
        """
        print(f"Node {self.node_id}: Synchronizing blockchain with the network.")
        last_epoch = max(block.epoch for block in self.blockchain)
        query_message = Message(
            MessageType.QUERY_MISSING_BLOCKS,
            {"last_epoch": last_epoch},
            self.port
        )
        self.broadcast_message(query_message)

    def vote_on_block(self, block):
        """
        Votes on a proposed block if it extends the longest notarized chain.

        This function checks whether the proposed block is valid and extends the chain.
        If so, it casts a vote and broadcasts the vote to other nodes in the network.
        """
        # Get the longest notarized chain's latest block
        longest_notarized_block = self.get_longest_notarized_chain()
        if longest_notarized_block and block.epoch <= longest_notarized_block.epoch:
            return  # Do not vote on older or same-epoch blocks

        with self.lock:
            block_hash = block.hash.hex()

            # Initialize vote counts and voted senders if not already present
            if block_hash not in self.vote_counts:
                self.vote_counts[block_hash] = 0
            if block_hash not in self.voted_senders:
                self.voted_senders[block_hash] = set()

            # Cast a vote if the node hasn't voted for this block yet
            if self.node_id not in self.voted_senders[block_hash]:
                self.vote_counts[block_hash] += 1
                self.voted_senders[block_hash].add(self.node_id)
                print(f"Node {self.node_id} voted for the proposed Block")
            else:
                return  # Skip voting again

        # Broadcast the vote to other nodes
        vote_message = Message.create_vote_message(block, self.node_id)
        threading.Thread(target=self.broadcast_message, args=(vote_message,), daemon=True).start()

        # Check if the block meets the criteria for notarization
        self.notarize_block(block)

    def notarize_block(self, block):
        """
        Notariza um bloco se ele receber mais votos do que n/2.
        Durante o período de confusão, evita finalizações prematuras.
        """
        with self.lock:
            block_hash = block.hash.hex()

            # Skip if the block is already notarized
            if block.epoch in self.notarized_blocks and self.notarized_blocks[block.epoch].hash == block.hash:
                return

            # Notarize if vote count exceeds quorum (n/2)
            if self.vote_counts.get(block_hash, 0) > self.total_nodes // 2:
                self.notarized_blocks[block.epoch] = block
                print(f"Node {self.node_id}: Block {block_hash} notarized in epoch {block.epoch} with transactions {list(block.transactions.keys())}")

                # Adicionar transações notarizadas
                for tx_id in block.transactions.keys():
                    self.notarized_tx_ids.add(tx_id)

                # Tentar finalizar blocos
                self.finalize_blocks()

    def finalize_blocks(self):
        """
        Finalizes blocks when three consecutive notarized blocks are observed.
        Ensures blocks are finalized in order, maintaining chain consistency.
        """
        notarized_epochs = sorted(self.notarized_blocks.keys())
        for i in range(len(notarized_epochs) - 2):  # At least three blocks
            first_epoch = notarized_epochs[i]
            second_epoch = notarized_epochs[i + 1]
            third_epoch = notarized_epochs[i + 2]

            # Check for three consecutive notarized blocks
            if (
                third_epoch == second_epoch + 1 and
                second_epoch == first_epoch + 1
            ):
                block_to_finalize = self.notarized_blocks[first_epoch]
                if block_to_finalize not in self.blockchain:
                    print(f"Node {self.node_id}: Finalizing Block {block_to_finalize.hash.hex()} in epoch {first_epoch}")
                    self.blockchain.extend(self.get_chain_to_block(block_to_finalize))
                    self.save_blockchain()
                    
    def get_chain_to_block(self, block):
        """
        Constructs the chain leading to the given block.

        This method traces back through the blockchain from the specified block to 
        the genesis block or an already finalized block in the node's blockchain.

        :param block: Block - The block to trace back from.
        :return: list - A list of blocks forming the chain up to the specified block.
        """
        chain = []
        current_block = block

        # Traverse back through the notarized blocks
        while current_block and current_block not in self.blockchain:
            # Insert the current block at the beginning of the chain
            chain.insert(0, current_block)

            # Find the parent block using the previous hash
            current_block = next(
                (b for b in self.notarized_blocks.values() if b.hash == current_block.previous_hash), None
            )
        
        return chain

    def get_longest_notarized_chain(self):
        with self.lock:
            if not self.notarized_blocks:
                return self.genesis_block 
            
            latest_epoch = max(self.notarized_blocks.keys())
            return self.notarized_blocks[latest_epoch]

    def add_transaction(self, transaction, epoch):
        """
        Adds a transaction to the list of pending transactions for the next epoch.

        Ensures the transaction is unique and not already included in the blockchain,
        notarized blocks, or pending transactions.

        :param transaction: Transaction - The transaction to add.
        :param epoch: int - The current epoch.
        """
        with self.lock:
            next_epoch = epoch + 1

            # Initialize the next epoch's transaction list if it doesn't exist
            if next_epoch not in self.pending_transactions:
                self.pending_transactions[next_epoch] = []

            # Check if the transaction is already in the blockchain
            for block in self.blockchain:
                if transaction.tx_id in block.transactions:
                    return

            # Check if the transaction is already notarized
            if transaction.tx_id in self.notarized_tx_ids:
                return

            # Check if the transaction is already in pending transactions
            for txs in self.pending_transactions.values():
                if any(tx.tx_id == transaction.tx_id for tx in txs):
                    return

            # Add the transaction to the pending list for the next epoch
            self.pending_transactions[next_epoch].append(transaction)

    def get_next_tx_id(self):
        """
        Generates a globally unique transaction ID.

        This method ensures that each transaction ID is unique across the node.

        :return: int - The next available transaction ID.
        """
        with self.tx_id_lock:
            self.global_tx_id += 1
            return self.global_tx_id

    def generate_random_transaction_for_epoch(self, epoch):
        """
        Creates and broadcasts a random transaction for the given epoch.

        This method generates a random transaction with random sender, receiver,
        and amount, then sends it to a randomly selected node.

        :param epoch: int - The epoch for which the transaction is generated.
        """
        sender = f"Client{random.randint(1, 100)}"  # Random sender
        receiver = f"Client{random.randint(1, 100)}"  # Random receiver
        amount = random.randint(1, 1000)  # Random amount

        # Generate a unique transaction ID
        tx_id = self.get_next_tx_id()
        transaction = Transaction(tx_id, sender, receiver, amount)

        # Select a random target node
        target_id = random.randint(0, self.total_nodes - 1)
        if target_id == self.node_id:
            # Add the transaction to the current node's pending transactions
            self.add_transaction(transaction, self.current_epoch)

            # Broadcast an ECHO message to notify the network
            echo_message = Message.create_echo_transaction_message(transaction, epoch, self.node_id)
            threading.Thread(
                target=self.broadcast_message,
                args=(echo_message,),
                daemon=True  # Use daemon thread so it ends with the program
            ).start()

    def generate_transactions_for_epoch(self, epoch):
        """
        Generates a random number of transactions for the specified epoch.

        :param epoch: int - The epoch for which transactions are to be generated.
        """
        num_transactions = random.randint(1, 3)  # Generate 1 to 3 transactions
        for _ in range(num_transactions):
            self.generate_random_transaction_for_epoch(epoch)

    def is_confusion_active(self, epoch):
        """
        Checks if the node is in the confusion period for a given epoch.

        :param epoch: int - The epoch to check.
        :return: bool - True if confusion is active, False otherwise.
        """
        return self.confusion_start <= epoch < self.confusion_start + self.confusion_duration

    def broadcast_message(self, message):
        serialized_message = message.serialize()
        for target_port in self.ports:
            if target_port != self.port:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect(('localhost', target_port))
                        s.sendall(serialized_message)
                except ConnectionRefusedError:
                    print(f"Node {self.node_id} could not connect to Node at port {target_port}")
                except Exception as e:
                    print(f"Node {self.node_id} encountered an error while broadcasting to port {target_port}: {e}")

    def send_message_to_port(self, target_port, message):
        """
        Sends a specific message to a target node via its port.

        :param target_port: int - The port of the target node.
        :param message: Message - The message to send.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', target_port))  # Establish a connection
                s.sendall(message.serialize())  # Send the serialized message
        except Exception as e:
            print(f"Node {self.node_id}: Error sending {message.type} to port {target_port}: {e}")

    def save_blockchain(self):
        """
        Saves the blockchain to a file in JSON format.

        This method serializes the blockchain into a list of dictionaries, where each block
        and its transactions are represented as nested dictionaries. The serialized data
        is then saved to a file named `blockchain_<node_id>.json`.

        The method does not use list comprehensions for better readability.
        """
        file_name = f"blockchain_{self.node_id}.json"  # File name specific to the node
        blockchain_data = []  # List to hold the serialized blocks

        # Iterate over each block in the blockchain to serialize it
        for block in self.blockchain:
            serialized_block = {
                "epoch": block.epoch,  # The epoch of the block
                "previous_hash": block.previous_hash.hex(),  # Convert hash to a readable hex string
                "transactions": [],  # Initialize an empty list for transactions
                "hash": block.hash.hex()  # Convert block's hash to hex string
            }

            # Serialize each transaction in the block
            for tx_id, tx in block.transactions.items():
                serialized_transaction = {
                    "tx_id": tx_id,  # Transaction ID
                    "sender": tx.sender,  # Sender's name
                    "receiver": tx.receiver,  # Receiver's name
                    "amount": tx.amount  # Amount being transferred
                }
                # Add the serialized transaction to the block's transaction list
                serialized_block["transactions"].append(serialized_transaction)

            # Add the serialized block to the blockchain data
            blockchain_data.append(serialized_block)

        # Write the serialized blockchain data to a file
        try:
            with open(file_name, 'w') as f:
                json.dump(blockchain_data, f, indent=4)  # Save with indentation for readability
        except Exception as e:
            print(f"Node {self.node_id}: Error saving blockchain to file: {e}")

    def load_blockchain(self):
        """
        Loads the blockchain from a file in JSON format.

        This method reads the serialized blockchain data from the file and reconstructs
        the blockchain and its transactions into their respective objects.
        """
        file_name = f"blockchain_{self.node_id}.json"  # File name specific to the node

        try:
            # Open and read the blockchain file
            with open(file_name, 'r') as f:
                blockchain_data = json.load(f)  # Load JSON data into a Python structure

            blockchain = []  # Temporary list to hold reconstructed blocks

            # Deserialize each block from the data
            for block_data in blockchain_data:
                block = Block(
                    epoch=block_data["epoch"],  # Epoch number of the block
                    previous_hash=bytes.fromhex(block_data["previous_hash"]),  # Convert hash back to bytes
                    transactions={
                        tx["tx_id"]: Transaction(
                            tx_id=tx["tx_id"],
                            sender=tx["sender"],
                            receiver=tx["receiver"],
                            amount=tx["amount"]
                        )
                        for tx in block_data["transactions"]  # Deserialize each transaction
                    }
                )
                blockchain.append(block)  # Add the reconstructed block to the list

            # Update the node's blockchain and notarized blocks
            self.blockchain = blockchain
            self.notarized_blocks = {block.epoch: block for block in self.blockchain}

        except FileNotFoundError:
            print(f"Node {self.node_id}: No saved blockchain file found.")
        except Exception as e:
            print(f"Node {self.node_id}: Error loading blockchain from file: {e}")

    def recover_blockchain(self):
        """
        Recovers the blockchain for a rejoining node.

        This method attempts to restore the blockchain by:
        1. Loading saved blocks from a file.
        2. Requesting missing blocks from other nodes via the QUERY_MISSING_BLOCKS message.
        3. Updating the current epoch to reflect the recovered state.
        """
        # Load blockchain from file
        self.load_blockchain()

        # Determine the last saved epoch from the loaded blockchain
        last_saved_epoch = max(block.epoch for block in self.blockchain) if self.blockchain else 0

        # Broadcast a query message to request missing blocks from the last saved epoch
        query_message = Message(
            MessageType.QUERY_MISSING_BLOCKS,
            {"last_epoch": last_saved_epoch},
            self.port
        )
        self.broadcast_message(query_message)

        # Wait for missing blocks to be recovered with a timeout of 15 seconds
        start_time = time.time()
        while not self.recovery_completed:
            if time.time() - start_time > 15:  # Stop waiting after 15 seconds
                break
            time.sleep(0.1)

        # Update the current epoch to one beyond the highest recovered epoch
        self.current_epoch = max(block.epoch for block in self.blockchain) + 1 if self.blockchain else 1

    def display_blockchain(self):
        """
        Displays the blockchain in a human-readable format.

        Iterates through each block and its transactions, printing their details
        to the console. This method helps visualize the state of the blockchain.
        """
        if not self.blockchain:
            print(f"Node {self.node_id}: Blockchain is empty.")
            return

        print(f"Node {self.node_id}: Current Blockchain:")

        # Iterate through each block in the blockchain
        for block in self.blockchain:
            print(f"Block (Epoch {block.epoch}):")  # Print the block's epoch
            print(f"  Hash: {block.hash.hex()}")  # Print the block's hash
            print(f"  Previous Hash: {block.previous_hash.hex()}")  # Print the previous block's hash
            print(f"  Transactions: {len(block.transactions)} transactions")  # Print transaction count

            # Iterate through each transaction in the block
            for tx_id, tx in block.transactions.items():
                print(f"    Transaction {tx_id}: from {tx.sender} to {tx.receiver} of {tx.amount} coins")
            
            # Add a separator for readability
            print("-" * 40) 
