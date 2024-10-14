from node import Node
from transaction import Transaction

class Network:
    def __init__(self):
        self.nodes : Node = []  # List of nodes in the network

    def add_node(self, node_id):
        new_node = Node(node_id)
        self.nodes.append(new_node)
        print(f"Node {node_id} added to the network.")

    def create_transaction(self, sender, receiver, transaction_id, amount):
        transaction = Transaction(sender, receiver, transaction_id, amount)
        if transaction.is_valid():
            print(f"Transaction {transaction_id} created and is valid.")
            return transaction
        else:
            print(f"Transaction {transaction_id} is invalid.")
            return None

    def start_epoch(self):
        for node in self.nodes:
            node.current_epoch += 1
            node.update_current_leader()  # Determine the leader for this epoch
            if node.leader:
                node.propose_block()  # Leader proposes a block
                node.finalize()  # Finalizes blocks if conditions are met

    def connect_peers(self):
        for node in self.nodes:
            node.peers = [n for n in self.nodes if n.node_id != node.node_id]
            print(f"Node {node.node_id} connected to peers: {[peer.node_id for peer in node.peers]}")

    def display_network(self):
        print("Current nodes in the blockchain network:")
        for node in self.nodes:
            print(node)