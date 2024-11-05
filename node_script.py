import socket
import sys
from message import Message, MessageType
from node import Node

def main():
    # Verify command-line arguments
    if len(sys.argv) < 4:
        print("Usage: node_script.py <node_id> <total_nodes> <port>")
        input("Press Enter to exit...")  # Keeps the window open if arguments are missing
        sys.exit(1)

    try:
        node_id = int(sys.argv[1])
        total_nodes = int(sys.argv[2])
        port = int(sys.argv[3])

        print(f"Starting Node {node_id} with total_nodes={total_nodes}, port={port}")

        # Initialize the Node without a network object
        network = None
        node = Node(node_id=node_id, total_nodes=total_nodes, network=network, port=port)

        # Signal readiness to the StreamletNetwork process
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ready_socket:
                ready_socket.connect(('localhost', 6000))  # Ready port for signaling
                ready_socket.sendall(b"READY")
            print(f"Node {node_id} sent READY signal.")
        except ConnectionRefusedError:
            print(f"Error: Could not connect to readiness port 6000 for Node {node_id}")
        except Exception as e:
            print(f"Unexpected error in readiness signaling for Node {node_id}: {e}")

        # Start listening for commands on the designated port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('localhost', port))
            sock.listen(1)
            print(f"Node {node_id} listening on port {port}")

            while True:
                conn, _ = sock.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        try:
                            # Use `deserialize` to convert data back into a `Message` object
                            message = Message.deserialize(data)
                            if message is None:
                                print(f"Deserialization failed in Node {node_id}. Ignoring message.")
                                continue
                            print(f"Node {node_id} received command: {message.type}")

                            # Handle different message types
                            if message.type == MessageType.START_PROPOSAL:
                                 # Validate sender and leader
                                if message.sender is not None and node_id == message.sender:
                                    epoch = message.content
                                    block = node.propose_block(epoch)
                                    print(f"Node {node_id} proposed block {block.hash}.")
                                    start_propose_message = Message.create_propose_message(block, node_id)

                                    # Create and broadcast the proposal message to other nodes
                                    propose_message = Message.create_propose_message(block, node_id)
                                    for target_port in range(port, port + total_nodes):
                                        if target_port != port:  # Avoid sending to itself
                                            try:
                                                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as propose_sock:
                                                    propose_sock.connect(('localhost', target_port))
                                                    propose_sock.sendall(propose_message.serialize())
                                                    print(f"Node {node_id} sent proposal to port {target_port}")
                                            except ConnectionRefusedError:
                                                print(f"Error: Could not connect to node on port {target_port} to send proposal.")
                                else:
                                    print(f"Node {node_id} is not the leader or sender is None; ignoring START_PROPOSAL.")

                            elif message.type == MessageType.PROPOSE:
                                block = message.content
                                node.vote_on_block(block)
                                print(f"Node {node_id} voted for block {block.hash}.")

                            elif message.type == MessageType.VOTE:
                                block = message.content
                                node.notarize_block(block)
                                print(f"Node {node_id} notarized block {block.hash}.")

                        except Exception as msg_err:
                            print(f"Deserialization error in Node {node_id}: {msg_err}")

    except Exception as e:
        print(f"Error in Node {node_id}: {e}")

    input("Press Enter to exit...")  # Prevent the terminal from closing instantly

if __name__ == "__main__":
    main()
