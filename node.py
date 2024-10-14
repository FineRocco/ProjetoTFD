import threading
from blockchain import Blockchain, Block, Transaction

class Node:
    TotalNodes = 5
    Epoch = 0
    DeltaEpoch = 5000

    def __init__(self, node_id):
        self.node_id = node_id  # Unique identifier for the node
        self.blockchain = Blockchain()  # Instance of the Blockchain class
        self.pending_transactions = []  # Transactions waiting to be included in a block
        self.current_epoch = 0   # Current epoch number
        self.votes = {}          # Dictionary to track votes for blocks
        self.leader = False      # Indicates if the node is the leader for the current epoch
        self.peers = []          # List of peers connected to this node

        # Initialize the blockchain with a genesis block
        genesis_block = Block(previous_hash='0', epoch=self.current_epoch, length=1, transactions=[])
        self.blockchain.add_block(genesis_block)  # Add the genesis block to the blockchain

        # Start a thread to process messages
        self.message_thread = threading.Thread(target=self.process_messages)
        self.message_thread.start()

    def __repr__(self):
        return (f"Node(node_id={self.node_id}, current_epoch={self.current_epoch}, "
                f"blockchain_length={len(self.blockchain.chain)}, status={self.status})")
        
    def process_message(self, message):
        """Process received messages by delegating to the message handler."""
        message.handle(self)

    def propose_block(self):
        """Propose a new block if the node is the leader."""
        if not self.leader:  # Only the leader can propose a block
            print(f"Node {self.node_id} is not the leader for epoch {self.current_epoch}.")
            return  

        proposed_block = Block(
            previous_hash=self.blockchain.chain[-1].calculate_hash() if self.blockchain.chain else "0",
            epoch=self.current_epoch,
            length=len(self.blockchain.chain) + 1,
            transactions=self.pending_transactions
        )
        self.broadcast(Message(msg_type="Propose", content=proposed_block, sender=self.node_id))
        print(f"Node {self.node_id} proposed a block for epoch {self.current_epoch}.")

    def vote_block(self, block):
        """Vote for a block and broadcast the vote to peers."""
        if not block.transactions:
            print(f"Node {self.node_id} cannot vote for an empty block.")
            return

        self.blockchain.add_block(block)  # Add the block to the blockchain
        self.broadcast(Message(msg_type="Vote", content=block, sender=self.node_id))
        print(f"Node {self.node_id} voted for block {block.length} in epoch {self.current_epoch}.")

    def notorize_block_votes(self, block):
        """Track votes for notarization and check if a block has enough votes."""
        if block not in self.votes:
            self.votes[block] = 0  
        self.votes[block] += 1

        if self.votes[block] > len(self.peers) / 2:
            self.blockchain.notarize_block(block)  # Move notarization to the Blockchain class
            self.blockchain.check_blockchain_notarization()  # Check notarization status

    def finalize(self):
        """Finalize blocks based on notarization and their sequential epochs."""
        self.blockchain.finalize()  # Delegate to the Blockchain class

    def add_transaction(self, transaction):
        """Add a transaction to the pending list if it's valid."""
        if isinstance(transaction, Transaction) and transaction.is_valid():
            self.pending_transactions.append(transaction)
            print(f"Node {self.node_id} added transaction {transaction.transaction_id}.")
        else:
            print(f"Node {self.node_id} failed to add transaction: Not a valid Transaction object.")

    def update_current_leader(self):
        """Update the leader status based on the current epoch."""
        self.leader = (self.node_id == self.current_epoch % len(self.peers))
        if self.leader:
            print(f"Node {self.node_id} is now the leader for epoch {self.current_epoch}.")

    def broadcast(self, message):
        """Broadcast a message to all connected peers."""
        for peer in self.peers:
            peer.process_message(message)
            print(f"Node {self.node_id} broadcasted message to Node {peer.node_id}.")
