# node_script.py

from datetime import datetime, timedelta
import threading
import socket
import time
import random
import sys
import signal

from node import Node

def main():
    """
    Main function for running a single node in the network.

    Usage: node_script.py <node_id> <total_nodes> <total_epochs> <delta> <port> <ports> <start_time>
    Example: python3 node_script.py 0 3 5 3 5000 5000,5001,5002 00:00
    """

    # Initialize variables to None
    node_id = None
    node = None
    listening_socket = None

    try:
        # Verify command-line arguments
        if len(sys.argv) < 8:
            print("Usage: node_script.py <node_id> <total_nodes> <total_epochs> <delta> <port> <ports> <start_time>")
            input("Press Enter to exit...")  # Keeps the window open if arguments are missing
            sys.exit(1)

        # Parse command-line arguments
        node_id = int(sys.argv[1])
        total_nodes = int(sys.argv[2])
        total_epochs = int(sys.argv[3])
        delta = int(sys.argv[4])
        port = int(sys.argv[5])
        ports = list(map(int, sys.argv[6].split(',')))  # List of network ports
        start_time = sys.argv[7]  

        print(f"Starting Node {node_id} with total_nodes={total_nodes}, port={port}")

        # Initialize the Node
        node = Node(
            node_id=node_id,
            total_nodes=total_nodes,
            total_epochs=total_epochs,
            delta=delta,
            port=port,
            ports=ports,
            start_time=start_time
        )

        # Create a listening socket
        listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listening_socket.bind(('localhost', port))
        listening_socket.listen(10)
        print(f"Node {node_id} listening on port {port}")

        node.running = True

        # Start listening for incoming messages in a separate thread
        listener_thread = threading.Thread(
            target=node.handle_incoming_messages,
            args=(listening_socket,),
            daemon=True
        )
        listener_thread.start()

        # Start the node's main protocol logic
        node.set_seed("toleratefaults")
        node.start()

        print(f"Node {node_id}: Running. Press Ctrl+C to exit.")

        # Define a graceful shutdown handler
        def shutdown_handler(signum, frame):
            print(f"\nNode {node_id}: Shutting down...")
            node.running = False
            if listening_socket:
                listening_socket.close()
            sys.exit(0)

        # Register the shutdown handler for SIGINT and SIGTERM
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        # Keep the main thread alive to allow daemon threads to run
        while True:
            time.sleep(1)

    except Exception as e:
        if node_id is not None:
            print(f"Error in Node {node_id}: {e}")
        else:
            print(f"Error in Node script: {e}")
    finally:
        try:
            if node is not None and node.running:
                node.running = False
            if listening_socket is not None:
                listening_socket.close()
                if node_id is not None:
                    print(f"Node {node_id}: Socket closed.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
