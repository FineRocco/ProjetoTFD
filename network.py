from lib2to3.pytree import Node


class Network:
    def __init__(self):
        self.nodes : Node = []

    def start_epoch(self):
        """Start a new epoch and let the leader propose blocks."""
        for node in self.nodes:
            node.current_epoch += 1
            node.update_current_leader(self.nodes.length)
            if node.leader:
                node.propose_block()
                node.finalize()

    def connect_peers(self):
        """Connect all nodes to each other as peers."""
        for node in self.nodes:
            node.peers = [n for n in self.nodes if n.node_id != node.node_id]
            print(f"Node {node.node_id} connected to peers: {[peer.node_id for peer in node.peers]}")

    def display_network(self):
        """Display the status of the network."""
        print("Current nodes in the blockchain network:")
        for node in self.nodes:
            print(node)
