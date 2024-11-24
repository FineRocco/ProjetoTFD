import socket
import sys
import threading
from message import Message
from node import Node

def main():
    """
    Main function for running a single node in the network.

    The function initializes the node, signals readiness to the Streamlet network,
    and listens for various message types (e.g., proposals, votes, notarizations, transactions).
    Based on the received message type, the node enqueues messages for processing.
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
        ports = list(map(int, sys.argv[6].split(',')))  # List of network ports
        start_time = sys.argv[7]  # Start time in HH:MM format

        print(f"Starting Node {node_id} with total_nodes={total_nodes}, port={port}")

        # Initialize the Node
        node = Node(node_id=node_id, total_nodes=total_nodes, total_epochs=total_epochs, delta=delta, port=port, ports=ports, start_time=start_time)
        node.set_seed("42")  # Example seed

        # Start listening for messages
        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('localhost', port))
                sock.listen()
                print(f"Node {node_id} listening on port {port}")

                while True:
                    conn, _ = sock.accept()
                    with conn:
                        data = conn.recv(4096)
                        if not data:
                            continue
                        message = Message.deserialize(data)
                        if message is None:
                            continue
                        node.message_queue.put(message)

        # Start the listening thread
        listener_thread = threading.Thread(target=listen)
        listener_thread.daemon = True
        listener_thread.start()

        # Keep the main thread alive
        node.join()

    except Exception as e:
        print(f"Error in Node {node_id}: {e}")

    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
