# main.py

from node import Node
from transaction import Transaction
import time

def main():
    """
    Main entry point to simulate the distributed system.
    """
    # Initialize nodes
    node1 = Node(node_id=1)
    node2 = Node(node_id=2)

    # Create transactions
    transaction1 = Transaction(sender=1, receiver=2, tx_id=1, amount=100.0)
    transaction2 = Transaction(sender=2, receiver=3, tx_id=2, amount=50.0)

    # Nodes receive transactions
    node1.receive_transaction(transaction1)
    node2.receive_transaction(transaction2)

    # Node 1 proposes a new block
    node1.propose_block()

    # Simulate a delay to allow for confusion and synchronization
    time.sleep(5)

    # Node 2 votes on block proposed by node 1
    node2.vote_for_block(node1.blockchain.chain[-1])

if __name__ == "__main__":
    main()
