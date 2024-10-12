from node import Node
from transaction import Transaction

def main():
    num_nodes = 5
    nodes = [Node(node_id=i, network=[]) for i in range(num_nodes)]

    # Setting up the network for each node
    for node in nodes:
        node.network = [n for n in nodes if n.node_id != node.node_id]

    transactions = [
        Transaction(sender=0, receiver=1, tx_id=1, amount=10.0),
        Transaction(sender=1, receiver=2, tx_id=2, amount=20.0),
        Transaction(sender=2, receiver=3, tx_id=3, amount=30.0)
    ]

    for tx in transactions:
        for node in nodes:
            node.receive_transaction(tx)

    epochs = 10
    for epoch in range(epochs):
        leader = nodes[epoch % num_nodes]
        leader.propose_block(epoch)

        for node in nodes:
            if node.node_id != leader.node_id:
                node.vote_on_block(leader.blockchain[-1])

        for node in nodes:
            node.finalize_blockchain()


if __name__ == "__main__":
    main()
