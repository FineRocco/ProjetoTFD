from block import Block

class MessageType:
    PROPOSE = "Propose"
    VOTE = "Vote"
    ECHO = "Echo"

class Message:
    def __init__(self, msg_type: str, content, sender: int):
        """
        Initializes a Message object.

        :param msg_type: The type of the message (Propose, Vote, Echo).
        :param content: The content of the message (Block or Message).
        :param sender: The ID of the sender node.
        """
        self.msg_type = msg_type
        self.content = content  # This can either be a Block or a Message
        self.sender = sender

    @staticmethod
    def create_propose_message(block: Block, sender: int):
        """
        Creates a Propose message.

        :param block: The Block to propose.
        :param sender: The sender node ID.
        :return: A Message object.
        """
        return Message(MessageType.PROPOSE, block, sender)

    @staticmethod
    def create_vote_message(block: Block, sender: int):
        """
        Creates a Vote message for the proposed block.

        :param block: The Block to vote on.
        :param sender: The sender node ID.
        :return: A Message object.
        """
        # Create a vote block without transactions to minimize size
        vote_block = Block(
            epoch=block.epoch,
            previous_hash=block.previous_hash,
            transactions=[]  # Strip transactions for vote
        )
        vote_block.votes = block.votes  
        vote_block.hash = block.hash    
        vote_block.length = block.length  

        return Message(MessageType.VOTE, vote_block, sender)

    @staticmethod
    def create_echo_message(message, sender: int):
        """
        Creates an Echo message.

        :param message: The message to echo.
        :param sender: The sender node ID.
        :return: A Message object.
        """
        return Message(MessageType.ECHO, message, sender)

    def __repr__(self):
        return f"<Message(type={self.msg_type}, sender={self.sender}, content={self.content})>"
