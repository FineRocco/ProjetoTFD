# node.py

from blockchain import Blockchain
from transaction import Transaction
from message import Message

class Node:
    def __init__(self, node_id: int):
        """
        Initializes a Node object.

        :param node_id: The ID of this node.
        """
        self.node_id = node_id
        self.blockchain = Blockchain()  # Use the Blockchain instance instead of a list for blockchain
        self.votes = {}  # Store votes for blocks
        self.received_blocks = []  # History of received blocks to support recovery and verification

    def propose_block(self):
        # Create a block using the blockchain instance
        new_block = self.blockchain.create_block(epoch=1)  # Example using epoch 1
        if new_block:
            new_block.mine_block(difficulty=2)
            # Propagate the new block to other nodes (logic to be implemented)
            print(f"Node {self.node_id} mined block with hash: {new_block.hash}")

    def receive_transaction(self, transaction: Transaction):
        # Add transaction to blockchain
        self.blockchain.add_transaction(transaction)

    def echo_block(self, block):
        # Broadcast the block to all other nodes
        print(f"Node {self.node_id} echoing block {block.hash}")

    def vote_for_block(self, block):
        if block not in self.votes:
            self.votes[block] = True
            # Broadcast the vote
            print(f"Node {self.node_id} voting for block {block.hash}")

# Example usage
if __name__ == "__main__":
    node = Node(node_id=1)
    transaction = Transaction(sender=1, receiver=2, tx_id=1, amount=50.0)
    node.receive_transaction(transaction)
    node.propose_block()
