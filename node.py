import threading
from block import Block
from message import Message
from transaction import Transaction

class Node: 
    TotalNodes = 5
    Votes = 0
    Epoch = 0
    DeltaEpoch = 5000

    def __init__(self, node_id):
        self.node_id = node_id  # Unique identifier for the node
        self.blockchain = []     # Local blockchain for the node
        self.pending_transactions = []  # Transactions pending to be included in a block
        self.current_epoch = 0   # Current epoch number
        self.notarized_blocks = []  # List of notarized blocks
        self.votes = {}          # Dictionary with Block --> Votes
        self.finalized_blocks = [] # List of finalized blocks
        self.leader = False      # Indicates if the node is the leader for the current epoch
        self.message_queue = []  # Queue to store received messages
        self.peers = []          # List of peers connected to this node
        self.status = "active"   # Current status of the node

        # Initialize blockchain with genesis block
        genesis_block = Block(previous_hash='0', epoch=self.current_epoch, length=1, transactions=[])
        self.blockchain.append(genesis_block)

    def __repr__(self):
        return (f"BlockchainNetworkNode(node_id={self.node_id}, current_epoch={self.current_epoch}, "
                f"blockchain_length={len(self.blockchain)}, status={self.status})")

    def process_message(self, message):
        if message.msg_type == "Propose":
            block = message.content
            print(f"Node {self.node_id} received a block proposal: {block}.")
            self.vote_block(block) 
        elif message.msg_type == "Echo":
            block = message.content
            print(f"Node {self.node_id} received an echo message for block {block.length}.")
        elif message.msg_type == "Vote":
            block = message.content
            print(f"Node {self.node_id} received a vote for block {block.length}.")
            self.notorize_block_votes(block)
        else:
            print(f"Node {self.node_id} received an unknown message type: {message.msg_type}.")

    def propose_block(self):
        if not self.leader:  # Only the leader can propose a block
            print(f"Node {self.node_id} is not the leader for epoch {self.current_epoch}.")
            return  

        proposed_block = Block(
            previous_hash=self.blockchain[-1].calculate_hash() if self.blockchain else "0",
            epoch=self.current_epoch,
            length=len(self.blockchain) + 1,
            transactions=self.pending_transactions
        )
        self.broadcast(Message(msg_type="Propose", content=proposed_block, sender=self.node_id))
        print(f"Node {self.node_id} proposed a block for epoch {self.current_epoch}.")

    def vote_block(self, block):
        if len(block.transactions) == 0:
            print(f"Node {self.node_id} cannot vote for an empty block.")
            return  
        if block.length > len(self.blockchain):
            self.blockchain.append(block)
        self.broadcast(Message(msg_type="Vote", content=block, sender=self.node_id))
        print(f"Node {self.node_id} voted for block in epoch {self.current_epoch}.")

    def notorize_block_votes(self, block):
        if block not in self.votes:
            self.votes[block] = 0  
        self.votes[block] += 1
        if self.votes[block] > len(self.peers) / 2:
            print(f"Node {self.node_id} notarized block {block.length}.")
            self.notarized_blocks.append(block)
            self.check_blockchain_notarization()

    def check_blockchain_notarization(self):
        for block in self.blockchain[1:]:
            if block not in self.notarized_blocks:
                print(f"Node {self.node_id}: Blockchain is not fully notarized yet.")
                return
        print(f"Node {self.node_id}: Blockchain is fully notarized and valid.")

    def finalize(self):
        if len(self.notarized_blocks) < 3:
            return
        for i in range(len(self.notarized_blocks) - 2):
            block1 = self.notarized_blocks[i]
            block2 = self.notarized_blocks[i + 1]
            block3 = self.notarized_blocks[i + 2]
            if (block1.epoch + 1 == block2.epoch and
                block2.epoch + 1 == block3.epoch):
                self.finalized_blocks.append(block2)
                print(f"Node {self.node_id} finalized block {block2.length} from epoch {block2.epoch}.")
                self.print_finalized_blocks()
                return

    def add_transaction(self, transaction):
        if isinstance(transaction, Transaction) and transaction.is_valid():
            self.pending_transactions.append(transaction)
            print(f"Node {self.node_id} added transaction {transaction.transaction_id}.")
        else:
            print(f"Node {self.node_id} failed to add transaction: Not a valid Transaction object.")

    def update_current_leader(self):
        if self.node_id == self.current_epoch % len(self.peers):
            self.leader = True
            print(f"Node {self.node_id} is now the leader for epoch {self.current_epoch}.")
        else:
            self.leader = False
            
    def broadcast(self, message):
        for peer in self.peers:
            peer.process_message(message)
            print(f"Node {self.node_id} broadcasted message to Node {peer.node_id}.")

    def print_finalized_blocks(self):
        print(f"Finalized blocks for Node {self.node_id}:")
        for block in self.finalized_blocks:
            print(f" - Block {block.length} from epoch {block.epoch}")

