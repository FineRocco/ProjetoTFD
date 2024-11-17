from datetime import datetime, timedelta
import random
import socket
import sys
import threading
import time
from message import Message, MessageType
from node import Node
from transaction import Transaction

def main():
    """
    Main function for running a single node in the network.

    The function initializes the node, signals readiness to the Streamlet network,
    and listens for various message types (e.g., proposals, votes, notarizations, transactions).
    Based on the received message type, the node performs actions like proposing blocks,
    voting, notarizing, and displaying the blockchain.

    Usage: node_script.py <node_id> <total_nodes> <total_epochs> <delta> <port> <ports>
    """
    
    # Verify command-line arguments
    if len(sys.argv) < 7:
        print("Usage: node_script.py <node_id> <total_nodes> <total_epochs> <delta> <port> <ports>")
        input("Press Enter to exit...")  # Keeps the window open if arguments are missing
        sys.exit(1)

    try:
        # Parse command-line arguments
        node_id = int(sys.argv[1])
        total_nodes = int(sys.argv[2])
        total_epochs = int(sys.argv[3])
        delta = int(sys.argv[4])
        port = int(sys.argv[5])
        ports = list(map(int, sys.argv[6].split(',')))  # List of network ports
        start_time = sys.argv[7]  # Start time in HH:MM format

        print(f"Starting Node {node_id} with total_nodes={total_nodes}, port={port}")

        # Initialize the Node
        node = Node(node_id=node_id, total_nodes=total_nodes, total_epochs = total_epochs, delta = delta, port=port, ports=ports, start_time=start_time)

        # Start listening for commands on the designated port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('localhost', port))
            sock.listen(10)
            print(f"Node {node_id} listening on port {port}")

            node.running = True

            # Start listening for incoming messages in a separate thread
            threading.Thread(target=node.handle_incoming_messages, args=(sock,), daemon=True).start()

            node.initialize_sockets()  # Set up connections with other nodes
            # Start the node's main protocol logic
            node.set_seed("toleranciaedfaltadeintrusoes", sock)
            node.start()
            print(f"Socket fileno: {sock.fileno()} (should be >= 0 if open)")


    except Exception as e:
        print(f"Error in Node {node_id}: {e}")

    input("Press Enter to exit...")  # Prevent the terminal from closing instantly

if __name__ == "__main__":
    main()