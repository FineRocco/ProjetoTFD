import random
import time
from block import Block
from transaction import Transaction
from message import Message, MessageType

class Node:
    def __init__(self, node_id: int, network):
        """
        Initializes a Node object.

        :param node_id: The ID of this node.
        :param network: A reference to the network (list of all nodes).
        """
        self.node_id = node_id
        self.blockchain = []  # The local blockchain.
        self.pending_transactions = []  # List of pending transactions.
        self.votes = {}  # Dictionary to store votes for blocks.
        self.notarized_blocks = set()  # Set of notarized blocks.
        self.network = network  # Reference to all nodes in the network.

    def receive_transaction(self, transaction: Transaction):
        """
        Receives a transaction and adds it to the pending transactions.

        :param transaction: The transaction received.
        """
        self.pending_transactions.append(transaction)
        print(f"Node {self.node_id} received transaction: {transaction}")

    def propose_block(self, epoch: int):
        """
        Proposes a new block with pending transactions if this node is the leader.

        :param epoch: The current epoch.
        :return: A Message object containing the proposed Block.
        """
        if self.node_id != self.get_leader(epoch):
            return None  # Not the leader, cannot propose a block.

        if not self.pending_transactions:
            print(f"Node {self.node_id} has no transactions to propose.")
            return None

        # Create a new block with the pending transactions
        previous_hash = self.blockchain[-1].hash if self.blockchain else b'0'  # Genesis block if none exists
        new_block = Block.generate_block(
            epoch=epoch,
            transactions=self.pending_transactions,
            previous_hash=previous_hash
        )

        # Clear pending transactions after proposing the block
        self.pending_transactions.clear()

        # Create a propose message and broadcast to all nodes
        propose_message = Message.create_propose_message(new_block, self.node_id)
        self.broadcast(propose_message)

        print(f"Node {self.node_id} proposed block at epoch {epoch}.")
        return propose_message

    def vote_on_block(self, block: Block):
        """
        Votes on a proposed block if it is valid and notarizes it if it gets enough votes.

        :param block: The block to vote on.
        """
        # Create a vote message for the given block
        vote_message = Message.create_vote_message(block, self.node_id)
        self.broadcast(vote_message)

        block_hash = block.hash
        if block_hash not in self.votes:
            self.votes[block_hash] = set()

        self.votes[block_hash].add(self.node_id)

        # Check if the block has enough votes to be notarized (2/3 majority)
        if len(self.votes[block_hash]) > (2 / 3) * len(self.network):
            print(f"Node {self.node_id} has notarized block {block_hash}.")
            self.notarized_blocks.add(block_hash)
            self.blockchain.append(block)
            self.check_for_finalization(block)
            
    def check_for_finalization(self, block):
        """
        Checks if three consecutive blocks are notarized and finalizes them.
        This is a simple finalization rule where if the last three blocks are notarized, the middle one is finalized.
        
        :param block: The last notarized block.
        """
        index = len(self.blockchain) - 1
        if index >= 2:
            if (self.blockchain[index - 2].hash in self.notarized_blocks and
                self.blockchain[index - 1].hash in self.notarized_blocks and
                self.blockchain[index].hash in self.notarized_blocks):
                print(f"Node {self.node_id} finalized block {self.blockchain[index - 1].hash}.")


    def broadcast(self, message: Message):
        """
        Broadcasts a message to all other nodes in the network.

        :param message: The message to broadcast.
        """
        for node in self.network:
            if node.node_id != self.node_id:
                node.handle_message(message)

    def get_leader(self, epoch: int) -> int:
        """
        Determines the leader for a given epoch using a simple round-robin approach.

        :param epoch: The current epoch.
        :return: The ID of the leader node.
        """
        return epoch % len(self.network)

    def handle_message(self, message: Message):
        """
        Handles an incoming message (Propose, Vote, or Echo).

        :param message: The message to handle.
        """
        if message.msg_type == MessageType.PROPOSE:
            block = message.content
            print(f"Node {self.node_id} received a block proposal for block {block.hash}.")
            self.vote_on_block(block)

        elif message.msg_type == MessageType.VOTE:
            block = message.content
            block_hash = block.hash
            if block_hash not in self.votes:
                self.votes[block_hash] = set()
            self.votes[block_hash].add(message.sender)

            if len(self.votes[block_hash]) > (2 / 3) * len(self.network):
                print(f"Node {self.node_id} notarized block {block_hash}.")
                self.notarized_blocks.add(block_hash)
                self.blockchain.append(block)
                self.check_for_finalization(block)

        elif message.msg_type == MessageType.ECHO:
            print(f"Node {self.node_id} received an Echo message.")
            
    def finalize_blockchain(self):
        """
        Check the blockchain for finalized blocks.
        In this simple model, we finalize blocks as they are notarized.
        """
        print(f"Node {self.node_id} finalized blockchain with {len(self.blockchain)} blocks.")
