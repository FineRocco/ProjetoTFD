from datetime import datetime, timedelta
import json
import random
import socket
import sys
import threading
import time
from block import Block
from message import Message, MessageType
from node import Node
from transaction import Transaction


def handle_incoming_messages(sock, node):
    """
    Listens for and processes incoming messages from other nodes.

    :param sock: socket.socket - The socket on which the node listens for connections.
    :param node: Node - The current node instance.
    """
    while True:
        conn, _ = sock.accept()  # Accept incoming connections
        with conn:
            # Extract transaction IDs from the blockchain and notarized sets
            blockchain_tx_ids = set()
            for block in node.blockchain:
                blockchain_tx_ids.update(block.transactions.keys())
            
            notarized_tx_ids = node.notarized_tx_ids

            # Deserialize the incoming message
            message = Message.deserialize_from_socket(conn, blockchain_tx_ids, notarized_tx_ids)
            if message is None:
                print(f"Deserialization failed in Node {node.node_id}. Ignoring message.")
                continue
            
            # Add the message to the processing queue
            with node.message_queue_lock:
                node.message_queue.append(message)

            # Start a thread to process the message queue
            threading.Thread(target=process_message_queue, args=(node,), daemon=True).start()

def process_message_queue(node):
    """
    Processes messages from the node's message queue.

    This function handles message ordering and delays during confusion periods.

    :param node: Node - The current node instance.
    """
    while True:
        with node.message_queue_lock:
            if node.message_queue:
                if node.is_confusion_active(node.current_epoch):
                    # Simulate delays and reordering during confusion
                    if random.random() < 0.5:  # 50% chance to delay processing
                        print(f"Node {node.node_id}: Delaying message processing during confusion.")
                        time.sleep(random.uniform(0.5, 2))
                    else:  # Simulate reordering
                        message = node.message_queue.pop(0)
                        node.message_queue.append(message)
                        print(f"Node {node.node_id}: Reordered message queue during confusion.")
                else:
                    # Process the first message in the queue
                    message = node.message_queue.pop(0)
                    threading.Thread(target=process_message, args=(node, message), daemon=True).start()
        time.sleep(0.1)  # Prevent CPU overutilization

def process_message(node, message):
    """
    Processes a single message based on its type.

    :param node: Node - The current node instance.
    :param message: Message - The message to process.
    """
    if message.type == MessageType.PROPOSE:
        # Handle a proposed block
        block = message.content
        node.vote_on_block(block)

    elif message.type == MessageType.VOTE:
        # Handle a vote for a block
        block = message.content
        block_hash = block.hash.hex()
        sender_id = message.sender

        print(f"Node {node.node_id}: Received Vote from Node {sender_id}")

        # Update vote tracking
        if block_hash not in node.vote_counts:
            node.vote_counts[block_hash] = 0
        if block_hash not in node.voted_senders:
            node.voted_senders[block_hash] = set()

        if sender_id not in node.voted_senders[block_hash]:
            node.vote_counts[block_hash] += 1
            node.voted_senders[block_hash].add(sender_id)

        # Check for block notarization
        node.notarize_block(block)

    elif message.type == MessageType.ECHO_TRANSACTION:
        # Handle echoed transactions
        content = message.content
        transaction = content['transaction']
        epoch = content['epoch']
        node.add_transaction(transaction, epoch)

    elif message.type == MessageType.QUERY_MISSING_BLOCKS:
        # Respond to missing block queries
        last_epoch = message.content.get("last_epoch")
        sender = message.sender

        missing_blocks = [
            node.notarized_blocks[epoch].to_dict()
            for epoch in range(last_epoch + 1, node.current_epoch + 1)
            if epoch in node.notarized_blocks
        ]

        response_message = Message(MessageType.RESPONSE_MISSING_BLOCKS, {"missing_blocks": missing_blocks}, node.node_id)
        node.send_message_to_port(sender, response_message)

    elif message.type == MessageType.RESPONSE_MISSING_BLOCKS:
        # Handle responses to missing block queries
        if node.recovery_completed:
            return
        
        missing_blocks = message.content.get("missing_blocks", [])
        for block_data in missing_blocks:
            block = block_data
            if block.epoch not in node.notarized_blocks:
                node.notarized_blocks[block.epoch] = block
                node.blockchain.append(block)
                print(f"Node {node.node_id}: Recovered Block for epoch {block.epoch}")

        if missing_blocks:
            latest_recovered_epoch = max(block.epoch for block in missing_blocks)
            if latest_recovered_epoch >= node.current_epoch - 1:
                node.recovery_completed = True
                print(f"Node {node.node_id}: Recovery completed after receiving missing blocks.")

def main():
    """
    Entry point for the node script. Initializes and starts a node.

    Usage:
        node_script.py <node_id> <port> <rejoin> <network_config_file>
    """
    if len(sys.argv) < 5:
        print("Usage: node_script.py <node_id> <port> <rejoin> <network_config_file>")
        sys.exit(1)

    # Parse command-line arguments
    node_id = int(sys.argv[1])
    port = int(sys.argv[2])
    rejoin = sys.argv[3].lower() == "true"
    network_config_file = sys.argv[4]

    # Load network configuration from a file
    try:
        with open(network_config_file, "r") as f:
            network_config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Network configuration file {network_config_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file {network_config_file}.")
        sys.exit(1)

    total_nodes = network_config["num_nodes"]
    total_epochs = network_config["total_epochs"]
    delta = network_config["delta"]
    start_time = network_config["start_time"]
    ports = network_config["ports"]
    confusion_start = network_config.get("confusion_start", None)
    confusion_duration = network_config.get("confusion_duration", None)

    # Initialize the Node
    node = Node(
        node_id=node_id,
        total_nodes=total_nodes,
        total_epochs=total_epochs,
        delta=delta,
        port=port,
        ports=ports,
        start_time=start_time,
        rejoin=rejoin,
        confusion_start=confusion_start,
        confusion_duration=confusion_duration
    )
    node.set_seed("toleranciaedfaltadeintrusoes")  # Seed for random leader selection

    # Start listening for incoming messages
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('localhost', port))
        sock.listen()
        print(f"Node {node_id} listening on port {port}")
        handle_incoming_messages(sock, node)

    input("Press Enter to exit...")  # Prevent the script from exiting immediately


if __name__ == "__main__":
    main()