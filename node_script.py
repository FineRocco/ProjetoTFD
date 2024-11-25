# node_script.py
import sys
from node import Node

def main():
    """
    Main function for running a single node in the network.
    Usage: node_script.py <node_id> <total_nodes> <total_epochs> <delta> <port> <ports> <start_time>
    """
    if len(sys.argv) < 8:
        print("Usage: node_script.py <node_id> <total_nodes> <total_epochs> <delta> <port> <ports> <start_time>")
        input("Press Enter to exit...")
        sys.exit(1)

    try:
        node_id = int(sys.argv[1])
        total_nodes = int(sys.argv[2])
        total_epochs = int(sys.argv[3])
        delta = int(sys.argv[4])
        port = int(sys.argv[5])
        ports = list(map(int, sys.argv[6].split(',')))
        start_time = sys.argv[7]

        print(f"Starting Node {node_id} with total_nodes={total_nodes}, port={port}")

        node = Node(node_id=node_id, total_nodes=total_nodes, total_epochs=total_epochs, delta=delta, port=port, ports=ports, start_time=start_time)
        node.set_seed("123456789")  # Set the seed for random leader selection

        # Start the node's network listener
        node.start_network_listener()

        # Start the node's main loop
        node.start()

        # Wait for the node to finish
        node.join()

    except Exception as e:
        print(f"Error in Node {node_id}: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
