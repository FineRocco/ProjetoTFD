import io
import pickle
from block import Block

class MessageType:
    PROPOSE = "Propose"
    VOTE = "Vote"
    ECHO = "Echo"
    START_PROPOSAL = "Start Proposal"

class Message:
    def __init__(self, type: str, content, sender: int):
        """
        Initializes a Message object.

        :param type: The type of the message (Propose, Vote, Echo, Start Proposal).
        :param content: The content of the message (Block, epoch, or another Message).
        :param sender: The ID of the sender node.
        """
        self.type = type
        self.content = content
        self.sender = sender

    @staticmethod
    def create_propose_message(block: Block, sender: int):
        return Message(MessageType.PROPOSE, block, sender)

    @staticmethod
    def create_vote_message(block: Block, sender: int):
        vote_block = Block(
            epoch=block.epoch,
            previous_hash=block.previous_hash,
            transactions=[]
        )
        vote_block.votes = block.votes
        vote_block.hash = block.hash
        vote_block.length = block.length
        return Message(MessageType.VOTE, vote_block, sender)

    @staticmethod
    def create_echo_message(message, sender: int):
        return Message(MessageType.ECHO, message, sender)
    
    @staticmethod
    def create_start_proposal_message(epoch: int, sender: int):
        """
        Creates a Start Proposal message.

        :param epoch: The epoch for the proposal.
        :param sender: The sender node ID.
        :return: A Message object.
        """
        return Message(MessageType.START_PROPOSAL, epoch, sender)

    def serialize(self):
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        """
        Deserializes bytes back into a Message object.

        :param data: The byte data to deserialize.
        :return: A Message object, or None if deserialization fails.
        """
        try:
            with io.BytesIO(data) as byte_stream:
                return pickle.load(byte_stream)
        except (pickle.PickleError, AttributeError) as e:
            print(f"Deserialization error: {e}")
            return None
