import socket
import sys
from message import Message, MessageType
from node import Node
from transaction import Transaction

def main():
    # Verify command-line arguments
    if len(sys.argv) < 5:
        print("Usage: node_script.py <node_id> <total_nodes> <port> <ports>")
        input("Press Enter to exit...")  # Keeps the window open if arguments are missing
        sys.exit(1)

    try:
        node_id = int(sys.argv[1])
        total_nodes = int(sys.argv[2])
        port = int(sys.argv[3])
        # Parse the list of ports passed as a single string argument
        ports = list(map(int, sys.argv[4].split(',')))

        print(f"Starting Node {node_id} with total_nodes={total_nodes}, port={port}")

        # Initialize the Node without a network object
        network = None
        node = Node(node_id=node_id, total_nodes=total_nodes, network=network, port=port, ports=ports)

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
                    # Use `deserialize_from_socket` to read and convert data directly from the socket
                    message = Message.deserialize_from_socket(conn)
                    if message is None:
                        print(f"Deserialization failed in Node {node_id}. Ignoring message.")
                        continue
                    print(f"Node {node_id} received command: {message.type}")

                    # Handle different message types
                    if message.type == MessageType.START_PROPOSAL:
                        # Validate sender and leader
                        if message.sender is not None and node_id == message.sender:
                            epoch = message.content
                            print(f"Node {node_id} is the leader for epoch {epoch}. Proceeding with proposal.")
                            
                            # Pass `node_id` as `leader_id` to `propose_block`
                            block = node.propose_block(epoch, leader_id=node_id)
                            if block:
                                print(f"Node {node_id} proposed block {block.hash.hex()}.")
                        else:
                            print(f"Node {node_id} is not the leader or sender is None; ignoring START_PROPOSAL.")

                    elif message.type == MessageType.PROPOSE:
                        block = message.content
                        node.vote_on_block(block)
                        print(f"Node {node_id} voted for block {block.hash.hex()}.")

                    elif message.type == MessageType.VOTE:
                        block = message.content
                        # Ensure a list is initialized for this epoch if not already present
                        if block.epoch not in node.votes:
                            node.votes[block.epoch] = []

                        # Append the block to the list of votes for this epoch if not already added
                        if not any(voted_block.hash == block.hash for voted_block in node.votes[block.epoch]):
                            node.votes[block.epoch].append(block)
                            block.votes += 1  # Increment the vote count for this block
                        
                        # Notarize the block if it has enough votes
                        node.notarize_block(block)
                        print(f"Node {node_id} checking block {block.hash.hex()} for notarization.")

                    elif message.type == MessageType.TRANSACTION:
                        # Extract transaction details and add to pending transactions
                        tx_data = message.content  # tx_data is expected to be a dictionary
                        transaction = Transaction(tx_data['tx_id'], tx_data['sender'], tx_data['receiver'], tx_data['amount'])
                        node.pending_transactions.append(transaction)
                        print(f"Node {node_id} added transaction {transaction.tx_id} to pending transactions.")

    except Exception as e:
        print(f"Error in Node {node_id}: {e}")

    input("Press Enter to exit...")  # Prevent the terminal from closing instantly

if __name__ == "__main__":
    main()
