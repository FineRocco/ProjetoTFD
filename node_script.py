from datetime import datetime, timedelta
import random
import socket
import sys
import threading
import time
from message import Message, MessageType
from node import Node
from transaction import Transaction


def handle_incoming_messages(sock, node):
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
                print(f"Deserialization failed in Node {node.node_id}. Ignoring message.")
                continue
            print(f"Node {node.node_id} received command: {message.type}")
            threading.Thread(target=process_message, args=(node, message), daemon=True).start()

def process_message(node, message):
    # Handle various message types
    if message.type == MessageType.PROPOSE:
        # Vote on the received proposed block
        block = message.content
        node.vote_on_block(block)
        print(f"Node {node.node_id} voted for block {block.hash.hex()}.")

    elif message.type == MessageType.VOTE:
        # Handle a vote on a block and update notarization if conditions are met
        block = message.content
        block_hash = block.hash.hex()
        sender_id = message.sender  # Ensure the message includes sender ID

        print(f"Node {node.node_id}: Received Vote from Node {sender_id} for Block {block_hash} in epoch {block.epoch}")

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
            print(f"Node {node.node_id}: Updated vote count for Block {block_hash} to {node.vote_counts[block_hash]}")
        else:
            print(f"Node {node.node_id}: Duplicate vote from Node {sender_id} for Block {block_hash}; ignoring.")

        # Check notarization condition
        node.notarize_block(block)
        print(f"Node {node.node_id}: Checking notarization for Block {block_hash} with updated votes = {node.vote_counts.get(block_hash, 0)}")

    elif message.type == MessageType.ECHO_NOTARIZE:
        # Update the node’s view of notarized blocks based on an echo message
        block = message.content
        if block.epoch not in node.notarized_blocks or node.notarized_blocks[block.epoch].hash != block.hash:
            node.notarized_blocks[block.epoch] = block
            # Adicionar tx_id das transações notarizadas via Echo
            for tx_id in block.transactions.keys():
                node.notarized_tx_ids.add(tx_id)
                #print(f"Node {node_id}: Transaction {tx_id} added to notarized_tx_ids via Echo.")
            #print(f"Node {node_id}: Updated notarization from Echo for Block {block.hash.hex()} in epoch {block.epoch}")
            node.finalize_blocks()  # Re-check finalization criteria

    elif message.type == MessageType.ECHO_TRANSACTION:
        # Add echoed transaction to pending transactions if it’s new
        content = message.content
        transaction = content['transaction']
        epoch = content['epoch']
        #print(f"Echoed Transaction ID: {transaction.tx_id}, Sender: {transaction.sender}, Receiver: {transaction.receiver}, Amount: {transaction.amount}, Epoch: {epoch}")
        node.add_transaction(transaction, epoch)
        #print(f"Node {node_id} added echoed transaction {transaction.tx_id} to pending transactions for epoch {epoch}.")

def main():
    """
    Main function for running a single node in the network.

    The function initializes the node, signals readiness to the Streamlet network,
    and listens for various message types (e.g., proposals, votes, notarizations, transactions).
    Based on the received message type, the node performs actions like proposing blocks,
    voting, notarizing, and displaying the blockchain.

    Usage: node_script.py <node_id> <total_nodes> <total_epochs> <delta> <port> <ports> <start_time>
    """
    
    # Verify command-line arguments
    if len(sys.argv) < 8:
        print("Usage: node_script.py <node_id> <total_nodes> <total_epochs> <delta> <port> <ports> <start_time>")
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
        node.set_seed("toleranciaedfaltadeintrusoes")  # Set the seed for random leader selection

        
        # Start listening for commands on the designated port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('localhost', port))
            sock.listen()
            print(f"Node {node_id} listening on port {port}")
            handle_incoming_messages(sock, node)



    except Exception as e:
        print(f"Error in Node {node_id}: {e}")

    input("Press Enter to exit...")  # Prevent the terminal from closing instantly

if __name__ == "__main__":
    main()