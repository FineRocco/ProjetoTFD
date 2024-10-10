import threading
import time
from message import Message, MessageType
from node import Node

class StreamletNetwork:
    def __init__(self, num_nodes, delta):
        """
        Initializes a network with multiple nodes.
        
        :param num_nodes: The number of nodes in the network.
        :param delta: The network delay parameter (∆), which will determine epoch duration.
        """
        self.num_nodes = num_nodes
        self.nodes = [Node(node_id=i, total_nodes=num_nodes, network=self) for i in range(num_nodes)]
        self.leader = 0  # Initially, node 0 is the leader
        self.global_tx_id = 0  # Global transaction counter
        self.tx_id_lock = threading.Lock()  # Lock to synchronize transaction ID generation
        self.delta = delta  # Set ∆, the network delay parameter
        self.epoch_duration = 2 * delta  # Epoch lasts for 2∆ rounds

    def start_network(self):
        """
        Starts all the nodes as separate threads.
        """
        for node in self.nodes:
            node.start()

    def stop_network(self):
        """
        Stops all nodes from running.
        """
        for node in self.nodes:
            node.running = False
            node.join()  # Wait for the thread to finish

    def next_leader(self):
        """
        Rotates the leader for the next epoch.
        """
        self.leader = (self.leader + 1) % len(self.nodes)

    def start_epoch(self, epoch):
        """
        Starts a new epoch in the network where the leader proposes a block.
        
        :param epoch: The current epoch number.
        """
        leader_node = self.nodes[self.leader]
        proposed_block = leader_node.propose_block(epoch)
        message = Message(MessageType.PROPOSE, proposed_block, leader_node.node_id)

        # Broadcast the proposed block to all other nodes
        for node in self.nodes:
            if node.node_id != leader_node.node_id:
                node.receive_message(message)

    def run(self, total_epochs):
        """
        Runs the consensus protocol for a number of epochs.
        
        :param total_epochs: The number of epochs to run.
        """
        for epoch in range(1, total_epochs + 1):
            print(f"=== Epoch {epoch} ===")
            self.start_epoch(epoch)
            # Rotate leader
            self.next_leader()

            # Finalize blocks at each node
            for node in self.nodes:
                node.finalize_blocks()

            # Wait for the epoch duration (2∆) before starting the next epoch
            time.sleep(self.epoch_duration)
        
        # After all epochs have completed, print the final blockchain for each node
        print("\n=== Final Blockchain for each node ===")
        for node in self.nodes:
            node.display_blockchain()

    def get_next_tx_id(self):
        """
        Provides a globally unique transaction ID.
        
        :return: The next available transaction ID.
        """
        with self.tx_id_lock:
            self.global_tx_id += 1
            return self.global_tx_id
        

