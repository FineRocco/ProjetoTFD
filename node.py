import threading
import socket
import time
import random
import sys

from block import Block
from message import Message, MessageType
from transaction import Transaction

class Node(threading.Thread):
    """
    Represents a blockchain node in a network running the Streamlet consensus protocol.
    Each node can propose, vote, and notarize blocks, and broadcasts messages to other nodes.
    """
    
    
    def __init__(self, node_id, total_nodes, network, port, ports):
        threading.Thread.__init__(self)
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.blockchain = []  # Local chain of notarized blocks
        self.pending_transactions = {}  
        self.vote_counts = {}  
        self.voted_senders = {} 
        self.notarized_blocks = {} 
        self.notarized_tx_ids = set() 
        self.network = network
        self.port = port
        self.ports = ports  
        print(f"Initialized Node {self.node_id} on port {self.port}") 
        self.running = True
        self.lock = threading.Lock()
        self.current_epoch = 1  
                
    def determine_epoch_for_transaction(self, transaction):
        if self.blockchain:
            return self.blockchain[-1].epoch + 1
        else:
            return 1 

    def propose_block(self, epoch, leader_id):
        """
        Proposes a new block at the start of an epoch if the node is the leader.
        """
        if self.node_id != leader_id:
            print(f"Node {self.node_id} is not the leader for epoch {epoch}.")
            return None

        # Retrieve the latest block in the notarized chain
        previous_block = self.get_longest_notarized_chain()
        previous_hash = previous_block.hash if previous_block else b'0' * 20

        with self.lock:
            block_transactions = self.pending_transactions.get(epoch, []).copy()
            new_block = Block(epoch, previous_hash, {tx.tx_id: tx for tx in block_transactions})
            
            if epoch in self.pending_transactions:
                del self.pending_transactions[epoch]
                print(f"Node {self.node_id}: Cleared pending_transactions for epoch {epoch} after proposing the block.")

        print(f"Node {self.node_id} proposes Block: {new_block.hash.hex()} with previous hash {previous_hash.hex()} and transactions {list(new_block.transactions.keys())}")

        # Create a Propose message and broadcast it
        propose_message = Message.create_propose_message(new_block, self.node_id)
        self.broadcast_message(propose_message)
        return new_block

    def vote_on_block(self, block):
        """
        Votes on a proposed block if it extends the longest notarized chain.

        :param block: Block - The proposed block.
        """
        print(f"Node {self.node_id}: Preparing to vote on Block {block.hash.hex()} with transactions: {list(block.transactions.keys())}")
        longest_notarized_block = self.get_longest_notarized_chain()
        if longest_notarized_block and block.epoch <= longest_notarized_block.epoch:
            print(f"Node {self.node_id}: Ignorando votação para Block {block.hash.hex()} em epoch {block.epoch} (epoch <= {longest_notarized_block.epoch})")
            return  

        with self.lock:
            block_hash = block.hash.hex()

            if block_hash not in self.vote_counts:
                self.vote_counts[block_hash] = 0

            if block_hash not in self.voted_senders:
                self.voted_senders[block_hash] = set()

            if self.node_id not in self.voted_senders[block_hash]:
                self.vote_counts[block_hash] += 1
                self.voted_senders[block_hash].add(self.node_id)
                print(f"Node {self.node_id} voted for Block {block_hash} in epoch {block.epoch}")
            else:
                print(f"Node {self.node_id} já votou para Block {block_hash} em epoch {block.epoch}")
                return

        # Broadcast vote to all nodes
        vote_message = Message.create_vote_message(block, self.node_id)
        self.broadcast_message(vote_message)

        # Check if the block should be notarized
        self.notarize_block(block)

    def notarize_block(self, block):
        """
        Notarizes a block if it receives more than n/2 votes, and notifies other nodes.

        :param block: Block - The block to notarize.
        """
        with self.lock:
            block_hash = block.hash.hex()
            print(f"Node {self.node_id}: Checking notarization for Block {block_hash} with votes = {self.vote_counts.get(block_hash, 0)}")

            # Check if this block is already notarized
            if block.epoch in self.notarized_blocks and self.notarized_blocks[block.epoch].hash == block.hash:
                print(f"Block {block_hash} has already been notarized in epoch {block.epoch}")
                return

            # Check if vote count meets quorum
            if self.vote_counts.get(block_hash, 0) > self.total_nodes // 2:
                self.notarized_blocks[block.epoch] = block
                print(f"Node {self.node_id}: Block {block_hash} notarized in epoch {block.epoch} with transactions {list(block.transactions.keys())}")

                for tx_id in block.transactions.keys():
                    self.notarized_tx_ids.add(tx_id)
                    print(f"Node {self.node_id}: Transaction {tx_id} added to notarized_tx_ids.")

                # Broadcast notarization to all nodes
                echo_message = Message.create_echo_notarize_message(block, self.node_id)
                self.broadcast_message(echo_message)
                self.finalize_blocks()

    def finalize_blocks(self):
        print(f"Node {self.node_id}: Checking for finalization. Current blockchain: {[(b.epoch, list(b.transactions.keys())) for b in self.blockchain]}")
        notarized_epochs = sorted(self.notarized_blocks.keys())
        print(f"Node {self.node_id}: Notarized epochs: {notarized_epochs}")
        
        for i in range(2, len(notarized_epochs)):
            if (notarized_epochs[i] == notarized_epochs[i - 1] + 1 and
                notarized_epochs[i - 1] == notarized_epochs[i - 2] + 1):
                finalized_block = self.notarized_blocks[notarized_epochs[i]]
                if finalized_block not in self.blockchain:
                    print(f"Node {self.node_id}: Finalizing Block {finalized_block.hash.hex()} in epoch {finalized_block.epoch}")
                    chain = self.get_chain_to_block(finalized_block)
                    self.blockchain.extend(chain)

    def get_chain_to_block(self, block):
        chain = []
        current_block = block
        while current_block and current_block not in self.blockchain:
            chain.insert(0, current_block)
            current_block = next(
                (b for b in self.notarized_blocks.values() if b.hash == current_block.previous_hash), None
            )
        return chain

    def get_longest_notarized_chain(self):
        with self.lock:
            if not self.notarized_blocks:
                return None  
            latest_epoch = max(self.notarized_blocks.keys())
            return self.notarized_blocks[latest_epoch]

    def add_transaction(self, transaction, epoch):
        with self.lock:
            next_epoch = epoch + 1
            print(f"Node {self.node_id}: Adding transaction {transaction.tx_id} to pending transactions for epoch {next_epoch}")
            print(f"Node {self.node_id}: Current pending transactions before add: {self.pending_transactions}")

            # Ensure the next epoch entry is initialized if it doesn't exist
            if next_epoch not in self.pending_transactions:
                self.pending_transactions[next_epoch] = []

            # Check if the transaction already exists in the blockchain or is notarized
            for block in self.blockchain:
                if transaction.tx_id in block.transactions:
                    print(f"Node {self.node_id}: Transaction {transaction.tx_id} already included in blockchain. Ignoring.")
                    return

            if transaction.tx_id in self.notarized_tx_ids:
                print(f"Node {self.node_id}: Transaction {transaction.tx_id} already notarized. Ignoring.")
                return

            # Avoid adding the transaction if it's already in the pending list
            for txs in self.pending_transactions.values():
                if any(tx.tx_id == transaction.tx_id for tx in txs):
                    print(f"Node {self.node_id}: Transaction {transaction.tx_id} already exists in pending transactions. Ignoring.")
                    return

            # Add the transaction to the pending list for the next epoch
            self.pending_transactions[next_epoch].append(transaction)
            print(f"Node {self.node_id} added transaction {transaction.tx_id} to pending transactions for epoch {next_epoch}.")

    def broadcast_message(self, message):
        serialized_message = message.serialize()
        for target_port in self.ports:
            if target_port != self.port:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        print(f"Node {self.node_id} broadcasting to port {target_port}")
                        s.connect(('localhost', target_port))
                        s.sendall(serialized_message)
                        print(f"Node {self.node_id} successfully broadcasted to port {target_port}")
                except ConnectionRefusedError:
                    print(f"Node {self.node_id} could not connect to Node at port {target_port}")
                except Exception as e:
                    print(f"Node {self.node_id} encountered an error while broadcasting to port {target_port}: {e}")

    def display_blockchain(self):
        if not self.blockchain:
            print(f"Node {self.node_id}: Blockchain is empty.")
            return

        print(f"Node {self.node_id}: Current Blockchain:")
        for index, block in enumerate(self.blockchain):
            print(f"Block {index + 1}:")
            print(f"  Hash: {block.hash.hex()}")
            print(f"  Previous Hash: {block.previous_hash.hex()}")
            print(f"  Epoch: {block.epoch}")
            print(f"  Transactions: {len(block.transactions)} transactions")
            
            for tx_id, tx in block.transactions.items():  # Unpack tx_id and Transaction object
                print(f"    Transaction {tx_id}: from {tx.sender} to {tx.receiver} of {tx.amount} coins")
            print("-" * 40)  # Separator for each block
