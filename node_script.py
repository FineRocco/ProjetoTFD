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
            with node.message_queue_lock:
                node.message_queue.append(message)

            threading.Thread(target=process_message_queue, args=(node,), daemon=True).start()

def process_message_queue(node):
    while True:
        with node.message_queue_lock:
            if node.message_queue:
                if node.is_confusion_active(node.current_epoch):
                    if random.random() < 0.5: 
                        print(f"Node {node.node_id}: Delaying message processing during confusion.")
                        time.sleep(random.uniform(0.5, 2)) 
                    else:
                        message = node.message_queue.pop(0)
                        node.message_queue.append(message)
                        print(f"Node {node.node_id}: Reordered message queue during confusion.")
                else:
                    message = node.message_queue.pop(0)
                    threading.Thread(target=process_message, args=(node, message), daemon=True).start()  # Troque self por node
        time.sleep(0.1)

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

    elif message.type == MessageType.ECHO_TRANSACTION:
        # Add echoed transaction to pending transactions if it’s new
        content = message.content
        transaction = content['transaction']
        epoch = content['epoch']
        #print(f"Echoed Transaction ID: {transaction.tx_id}, Sender: {transaction.sender}, Receiver: {transaction.receiver}, Amount: {transaction.amount}, Epoch: {epoch}")
        node.add_transaction(transaction, epoch)
        #print(f"Node {node_id} added echoed transaction {transaction.tx_id} to pending transactions for epoch {epoch}.")

    elif message.type == MessageType.QUERY_MISSING_BLOCKS:
        # Respond with missing blocks
        last_epoch = message.content.get("last_epoch")
        sender = message.sender
        print(f"Node {node.node_id}: Received QUERY_MISSING_BLOCKS from Node {sender} with last_epoch {last_epoch}")

        # Collect missing blocks from last_epoch + 1 to current_epoch
        missing_blocks = [
            node.notarized_blocks[epoch].to_dict()
            for epoch in range(last_epoch + 1, node.current_epoch + 1)
            if epoch in node.notarized_blocks
        ]

        # Debugging: Print the missing blocks
        print(f"Node {node.node_id}: Missing blocks to send to Node {sender}:")
        for block in missing_blocks:
            print(f"  Epoch {block['epoch']}, Hash: {block['hash']}")

        # Send RESPONSE_MISSING_BLOCKS with the missing blocks
        response_message = Message(MessageType.RESPONSE_MISSING_BLOCKS, {"missing_blocks": missing_blocks}, node.node_id)
        node.send_message_to_port(sender, response_message)

    elif message.type == MessageType.RESPONSE_MISSING_BLOCKS:
        if node.recovery_completed:
            print(f"Node {node.node_id}: Recovery already completed. Ignoring RESPONSE_MISSING_BLOCKS.")
            return
        
        missing_blocks = message.content.get("missing_blocks", [])
        # Add the missing blocks to the blockchain
        for block_data in missing_blocks:
            block = block_data
            if block.epoch not in node.notarized_blocks:
                node.notarized_blocks[block.epoch] = block
                node.blockchain.append(block)
                print(f"Node {node.node_id}: Recovered Block for epoch {block.epoch}")

        # Check if recovery is now complete
        if missing_blocks:
            latest_recovered_epoch = max(block.epoch for block in missing_blocks)
            if latest_recovered_epoch >= node.current_epoch - 1:
                node.recovery_completed = True
                print(f"Node {node.node_id}: Recovery completed after receiving missing blocks.")

def main():
    # Check if command-line arguments are provided
    if len(sys.argv) < 5:
        print("Usage: node_script.py <node_id> <port> <rejoin> <network_config_file>")
        sys.exit(1)

    # Parse command-line arguments
    node_id = int(sys.argv[1])
    port = int(sys.argv[2])
    rejoin = sys.argv[3].lower() == "true"  # Convert "True"/"False" to a boolean
    network_config_file = sys.argv[4]

    # Load network configuration
    try:
        with open(network_config_file, "r") as f:
            network_config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Network configuration file {network_config_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file {network_config_file}.")
        sys.exit(1)

    # Extract network configuration
    total_nodes = network_config["num_nodes"]
    total_epochs = network_config["total_epochs"]
    delta = network_config["delta"]
    start_time = network_config["start_time"]
    ports = network_config["ports"]
    confusion_start = network_config.get("confusion_start", None)
    confusion_duration = network_config.get("confusion_duration", None)

    print(f"Starting Node {node_id} with the following configuration:")
    print(f"Node ID: {node_id}")
    print(f"Port: {port}")
    print(f"Rejoin: {rejoin}")
    print("Network Info:")
    print(json.dumps(network_config, indent=4))

    # Initialize the Node
    node = Node(node_id=node_id, total_nodes=total_nodes, total_epochs = total_epochs, delta = delta, port=port, ports=ports, start_time=start_time, rejoin=rejoin, confusion_start=confusion_start, confusion_duration=confusion_duration)
    node.set_seed("toleranciaedfaltadeintrusoes")  # Set the seed for random leader selection

    # Start listening for commands on the designated port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('localhost', port))
        sock.listen()
        print(f"Node {node_id} listening on port {port}")
        handle_incoming_messages(sock, node)

    input("Press Enter to exit...")  # Prevent the terminal from closing instantly

if __name__ == "__main__":
    main()