import socket
import sys
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

    Usage: node_script.py <node_id> <total_nodes> <port> <ports>
    """
    
    # Verify command-line arguments
    if len(sys.argv) < 5:
        print("Usage: node_script.py <node_id> <total_nodes> <port> <ports>")
        input("Press Enter to exit...")  # Keeps the window open if arguments are missing
        sys.exit(1)

    try:
        # Parse command-line arguments
        node_id = int(sys.argv[1])
        total_nodes = int(sys.argv[2])
        port = int(sys.argv[3])
        ports = list(map(int, sys.argv[4].split(',')))  # List of network ports

        print(f"Starting Node {node_id} with total_nodes={total_nodes}, port={port}")

        # Initialize the Node without a network object
        network = None
        node = Node(node_id=node_id, total_nodes=total_nodes, network=network, port=port, ports=ports)

        # Signal readiness to the StreamletNetwork process
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ready_socket:
                ready_socket.connect(('localhost', 6000))  # Port for readiness signaling
                ready_socket.sendall(b"READY")
            print(f"Node {node_id} sent READY signal.")
        except ConnectionRefusedError:
            print(f"Error: Could not connect to readiness port 6000 for Node {node_id}")
        except Exception as e:
            print(f"Unexpected error in readiness signaling for Node {node_id}: {e}")

        # Start listening for commands on the designated port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('localhost', port))
            sock.listen()
            print(f"Node {node_id} listening on port {port}")

            # Main loop for handling incoming messages
            while True:
                conn, _ = sock.accept()
                with conn:
                    blockchain_tx_ids = set()
                    for block in node.blockchain:
                        blockchain_tx_ids.update(block.transactions.keys())
                    
                    notarized_tx_ids = node.notarized_tx_ids

                    message = Message.deserialize_from_socket(conn, blockchain_tx_ids, notarized_tx_ids)
                    if message is None:
                        print(f"Deserialization failed in Node {node_id}. Ignoring message.")
                        continue
                    print(f"Node {node_id} received command: {message.type}")

                    # Handle various message types
                    if message.type == MessageType.START_PROPOSAL:
                        # Propose a new block if the node is the leader for the current epoch
                        if message.sender is not None and node_id == message.sender:
                            epoch = message.content
                            print(f"Node {node_id} is the leader for epoch {epoch}. Proceeding with proposal.")
                            block = node.propose_block(epoch, leader_id=node_id)
                            if block:
                                print(f"Node {node_id} proposed block {block.hash.hex()}.")
                        else:
                            print(f"Node {node_id} is not the leader or sender is None; ignoring START_PROPOSAL.")

                    elif message.type == MessageType.PROPOSE:
                        # Vote on the received proposed block
                        block = message.content
                        node.vote_on_block(block)
                        print(f"Node {node_id} voted for block {block.hash.hex()}.")

                    elif message.type == MessageType.VOTE:
                        # Handle a vote on a block and update notarization if conditions are met
                        block = message.content
                        block_hash = block.hash.hex()
                        sender_id = message.sender  # Ensure the message includes sender ID

                        print(f"Node {node_id}: Received Vote from Node {sender_id} for Block {block_hash} in epoch {block.epoch}")

                        # Initialize vote tracking structures
                        if block_hash not in node.vote_counts:
                            node.vote_counts[block_hash] = 0
                        if block_hash not in node.voted_senders:
                            node.voted_senders[block_hash] = set()

                        # Check if this sender has already voted for this block
                        if sender_id not in node.voted_senders[block_hash]:
                            # Add vote and update vote counts
                            node.vote_counts[block_hash] += 1
                            node.voted_senders[block_hash].add(sender_id)
                            print(f"Node {node_id}: Updated vote count for Block {block_hash} to {node.vote_counts[block_hash]}")
                        else:
                            print(f"Node {node_id}: Duplicate vote from Node {sender_id} for Block {block_hash}; ignoring.")

                        # Check notarization condition
                        node.notarize_block(block)
                        print(f"Node {node_id}: Checking notarization for Block {block_hash} with updated votes = {node.vote_counts.get(block_hash, 0)}")

                    elif message.type == MessageType.ECHO_NOTARIZE:
                        # Update the node’s view of notarized blocks based on an echo message
                        block = message.content
                        if block.epoch not in node.notarized_blocks or node.notarized_blocks[block.epoch].hash != block.hash:
                            node.notarized_blocks[block.epoch] = block
                            # Adicionar tx_id das transações notarizadas via Echo
                            for tx_id in block.transactions.keys():
                                node.notarized_tx_ids.add(tx_id)
                                print(f"Node {node_id}: Transaction {tx_id} added to notarized_tx_ids via Echo.")
                            print(f"Node {node_id}: Updated notarization from Echo for Block {block.hash.hex()} in epoch {block.epoch}")
                            node.finalize_blocks()  # Re-check finalization criteria

                    elif message.type == MessageType.TRANSACTION:
                        # Process and broadcast a new transaction
                        content = message.content
                        transaction = content['transaction']
                        epoch = content['epoch']
                        print(f"Transaction ID: {transaction.tx_id}, Sender: {transaction.sender}, Receiver: {transaction.receiver}, Amount: {transaction.amount}, Epoch: {epoch}")
                        
                        node.add_transaction(transaction, epoch)
                        echo_message = Message.create_echo_transaction_message(transaction, epoch, node_id)
                        node.broadcast_message(echo_message)

                    elif message.type == MessageType.ECHO_TRANSACTION:
                        # Add echoed transaction to pending transactions if it’s new
                        content = message.content
                        transaction = content['transaction']
                        epoch = content['epoch']
                        print(f"Echoed Transaction ID: {transaction.tx_id}, Sender: {transaction.sender}, Receiver: {transaction.receiver}, Amount: {transaction.amount}, Epoch: {epoch}")
                        node.add_transaction(transaction, epoch)
                        print(f"Node {node_id} added echoed transaction {transaction.tx_id} to pending transactions for epoch {epoch}.")

                    elif message.type == MessageType.DISPLAY_BLOCKCHAIN:
                        node.display_blockchain()

    except Exception as e:
        print(f"Error in Node {node_id}: {e}")

    input("Press Enter to exit...")  # Prevent the terminal from closing instantly

if __name__ == "__main__":
    main()