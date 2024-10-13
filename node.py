import threading
from block import Block
from transaction import Transaction
from message import Message, MessageType

class Node(threading.Thread):
    def __init__(self, node_id: int, network):
        """
        Initializes a Node object and starts a thread for it.

        :param node_id: The unique ID of the node.
        :param network: A reference to the network (list of all nodes).
        """
        threading.Thread.__init__(self)
        self.node_id = node_id
        self.blockchain = []  # Local chain of notarized blocks
        self.pending_transactions = []  # List of pending transactions
        self.votes = {}  # Keeps track of votes for each block by epoch
        self.notarized_blocks = {}  # Blocks that received n/2 votes
        self.network = network  # Reference to all nodes in the network
        self.lock = threading.Lock()  # Lock for thread-safe operations

    def propose_block(self, epoch: int):
        """
        Proposes a new block at the start of an epoch.

        :param epoch: The current epoch number.
        """
        if self.node_id != self.get_leader(epoch):
            print(f"Node {self.node_id} is not the leader for epoch {epoch}, cannot propose a block.")
            return None
        
        previous_block = self.get_longest_notarized_chain()
        previous_hash = previous_block.hash if previous_block else b'0' * 20

        with self.lock:
            new_block = Block.generate_block(
                epoch=epoch,
                transactions=self.pending_transactions,
                previous_hash=previous_hash
            )
            self.pending_transactions.clear()  # Clear after proposing

        print(f"Node {self.node_id} proposes Block: {new_block.hash.hex()}")
        
        # Create and broadcast a Propose message
        propose_message = Message.create_propose_message(new_block, self.node_id)
        self.broadcast_message(propose_message)

        return new_block

    def vote_on_block(self, block: Block):
        """
        Votes on a proposed block if it extends the longest notarized chain.

        :param block: The proposed block.
        """
        longest_notarized_block = self.get_longest_notarized_chain()
        if longest_notarized_block and block.length <= longest_notarized_block.length:
            print(f"Node {self.node_id} does not vote for Block {block.hash.hex()} (not extending the chain).")
            return  # Do not vote for shorter or equal-length chains
        
        with self.lock:
            if block.epoch not in self.votes:
                self.votes[block.epoch] = []

            # Check if this node has already voted for this block in this epoch
            if any(voted_block.hash == block.hash for voted_block in self.votes[block.epoch]):
                print(f"Node {self.node_id} has already voted for Block {block.hash.hex()} in epoch {block.epoch}")
                return  # Node has already voted for this block in this epoch

            # Add the block to the list of voted blocks for this epoch
            self.votes[block.epoch].append(block)
            block.votes += 1  # Increment the block's vote count
            print(f"Node {self.node_id} voted for Block {block.hash.hex()} in epoch {block.epoch}")

        # Broadcast vote to all other nodes
        vote_message = Message.create_vote_message(block, self.node_id)
        self.broadcast_message(vote_message)
        
    def notarize_block(self, block: Block):
        """
        Notarizes a block if it receives more than n/2 votes.

        :param block: The block to notarize.
        """
        with self.lock:
            if block.epoch in self.notarized_blocks and self.notarized_blocks[block.epoch].hash == block.hash:
                print(f"Block {block.hash.hex()} has already been notarized in epoch {block.epoch}")
                return  # Block has already been notarized

            # Notarize the block if it has more than n/2 votes
            if block.votes > len(self.network) // 2:
                self.notarized_blocks[block.epoch] = block
                print(f"Block {block.hash.hex()} notarized in epoch {block.epoch}")

        self.finalize_blocks()

    def finalize_blocks(self):
        """
        Finalizes blocks when three consecutive blocks are notarized.
        """
        with self.lock:
            notarized_epochs = sorted(self.notarized_blocks.keys())
            for i in range(1, len(notarized_epochs) - 1):
                if (notarized_epochs[i] == notarized_epochs[i-1] + 1 and
                        notarized_epochs[i+1] == notarized_epochs[i] + 1):
                    finalized_block = self.notarized_blocks[notarized_epochs[i]]
                    print(f"Node {self.node_id} finalizes Block {finalized_block.hash.hex()}")
                    self.blockchain.append(finalized_block)

    def receive_message(self, message: Message):
        """
        Handles incoming messages (Propose, Vote, or Echo).

        :param message: The message to handle.
        """
        if message.msg_type == MessageType.PROPOSE:
            print(f"Node {self.node_id} received proposed Block {message.content.hash.hex()}")
            self.vote_on_block(message.content)

        elif message.msg_type == MessageType.VOTE:
            self.notarize_block(message.content)

            # Send Echo message to other nodes after receiving a Vote message
            echo_message = Message.create_echo_message(message, self.node_id)
            self.broadcast_message(echo_message)

    def broadcast_message(self, message: Message):
        """
        Sends a message to all other nodes in the network.

        :param message: The message to broadcast.
        """
        for node in self.network:
            if node.node_id != self.node_id:
                node.receive_message(message)

    def get_longest_notarized_chain(self) -> Block:
        """
        Returns the last block in the longest notarized chain.
        Traverses from the latest notarized block backwards to find the longest chain.

        :return: The last block of the longest notarized chain or None.
        """
        with self.lock:
            if not self.notarized_blocks:
                return None  # No notarized blocks yet

            # Find the latest epoch with a notarized block
            latest_epoch = max(self.notarized_blocks.keys())
            longest_chain_tip = self.notarized_blocks[latest_epoch]

            # Traverse backward through the chain to find the longest chain
            chain = []
            current_block = longest_chain_tip
            while current_block:
                chain.append(current_block)

                # Find the parent block
                parent_block = None
                with self.lock:
                    for block in self.notarized_blocks.values():
                        if block.hash == current_block.previous_hash:
                            parent_block = block
                            break

                current_block = parent_block

            return chain[-1] if chain else None

    def get_leader(self, epoch: int) -> int:
        """
        Determines the leader for a given epoch using a simple round-robin approach.

        :param epoch: The current epoch.
        :return: The ID of the leader node.
        """
        return epoch % len(self.network)