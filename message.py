# message.py

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
        # Create a message with the VOTE type and send the block without its transactions
        empty_block = Block(
            hash=block.hash,
            epoch=block.epoch,
            length=block.length,
            transactions=[]  # Remove transactions for voting
        )
        return Message(MessageType.VOTE, empty_block, sender)

    @staticmethod
    def create_echo_message(message, sender: int):
        """
        Creates an Echo message.

        :param message: The message to echo.
        :param sender: The sender node ID.
        :return: A Message object.
        """
        # Echoing an existing message
        return Message(MessageType.ECHO, message, sender)
