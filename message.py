class Message:
    def __init__(self, msg_type, content, sender):
        self.msg_type = msg_type  # Type of message (Propose, Echo, Vote)
        self.content = content     # Content of the message (usually a Block)
        self.sender = sender       # Sender node ID

    def handle(self,  node):
        """Handle the message based on its type."""
        if self.msg_type == "Propose":
            print(f"Node {node.node_id} received a block proposal from {self.sender}: {self.content}.")
            node.vote_block(self.content)
        elif self.msg_type == "Echo":
            print(f"Node {node.node_id} received an echo message for block {self.content.length} from {self.sender}.")
        elif self.msg_type == "Vote":
            print(f"Node {node.node_id} received a vote for block {self.content.length} from {self.sender}.")
            node.notorize_block_votes(self.content)
        else:
            print(f"Node {node.node_id} received an unknown message type: {self.msg_type}.")