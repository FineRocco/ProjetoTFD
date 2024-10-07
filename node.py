# node.py

from block import Block
from transaction import Transaction
from message import Message

class Node:
    def __init__(self, node_id: int):
        """
        Initializes a Node object.

        :param node_id: The ID of this node.
        """
        self.node_id = node_id
        self.blockchain = []  # The local blockchain.
        self.pending_transactions = []  # List of pending transactions.
        self.votes = {}  # Dictionary to store votes for blocks.

    def receive_transaction(self, transaction: Transaction):
        """
        Receives a transaction and adds it to the pending transactions.

        :param transaction: The transaction received.
        """
        # To Do: Implement transaction reception logic
        pass

    def propose_block(self, epoch: int):
        """
        Proposes a new block with pending transactions.

        :param epoch: The current epoch.
        :return: A Message object containing the proposed Block.
        """
        # To Do: Implement block proposal logic
        pass

    def vote_on_block(self, block: Block):
        """
        Votes on a proposed block.

        :param block: The block to vote on.
        :return: A Message object containing the vote.
        """
        # To Do: Implement block voting logic
        pass

    def finalize_blockchain(self):
        """
        Finalizes blocks based on consecutive notarized blocks.

        :return: The finalized blockchain.
        """
        # To Do: Implement blockchain finalization logic
        pass

    def handle_message(self, message: Message):
        """
        Handles an incoming message (Propose, Vote, or Echo).

        :param message: The message to handle.
        """
        # To Do: Implement message handling logic
        pass
