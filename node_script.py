import socket
import sys
from message import Message
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
                        command = data.decode('utf-8')
                        print(f"Node {node_id} received command: {command}")
                        if command == "PROPOSE":
                            # Call propose_block for the current epoch
                            node.propose_block(epoch=0)  # Set a default epoch value if needed
                        elif command.startswith("VOTE"):
                            # Deserialize the block from the command and vote on it
                            block = Message.deserialize(data[5:])  # Assuming the block is attached after "VOTE "
                            node.vote_on_block(block)
                        elif command == "FINALIZE":
                            node.finalize_blocks()
                            print(f"Node {node_id} finalized blocks.")
                        elif command == "STOP":
                            print(f"Stopping Node {node_id}")
                            break  # Exit loop and stop the process
                        # Handle other commands as needed

    except Exception as e:
        print(f"Error in Node {node_id}: {e}")

    input("Press Enter to exit...")  # Prevent the terminal from closing instantly

if __name__ == "__main__":
    main()
