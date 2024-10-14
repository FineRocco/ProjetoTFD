from enum import Enum

from ProjetoTFD.block import Block

class MessageType(Enum):
    PROPOSE = "Propose"
    VOTE = "Vote"
    ECHO = "Echo"

class Message:
    def __init__(self, msg_type: MessageType, content, sender: int):
        self.msg_type = msg_type  # Type of the message (Propose, Vote, Echo)
        self.content = content    # Content of the message (Block or another Message)
        self.sender = sender      # Node ID of the sender

    def __repr__(self):
        return f"Message(type={self.msg_type}, sender={self.sender}, content={self.content})"

    def handle(self, node: Block):
        """Process the message based on its type."""
        if self.msg_type == MessageType.PROPOSE:
            self.handle_propose(node)
        elif self.msg_type == MessageType.VOTE:
            self.handle_vote(node)
        elif self.msg_type == MessageType.ECHO:
            self.handle_echo(node)
        else:
            print(f"Node {node.node_id} received an unknown message type: {self.msg_type}.")

    def handle_propose(self, node: Block):
        """Handle the 'Propose' message, where a block is proposed."""
        block = self.content
        print(f"Node {node.node_id} received a block proposal from {self.sender}: {block}.")
        node.vote_block(block)  # Node votes for the proposed block

    def handle_vote(self, node: Block):
        """Handle the 'Vote' message, where a node votes for a block."""
        block = self.content
        if block.transactions:
            print(f"Node {node.node_id}: Transactions field should be empty in vote message. Clearing transactions.")
            block.transactions = []  # Ensure transactions field is empty when voting
        print(f"Node {node.node_id} received a vote for block {block.length} from {self.sender}.")
        node.notorize_block_votes(block)

    def handle_echo(self, node: Block):
        """Handle the 'Echo' message, which echoes back a message."""
        echoed_message = self.content
        print(f"Node {node.node_id} received an echo message from {self.sender}: {echoed_message}.")
        # To do
