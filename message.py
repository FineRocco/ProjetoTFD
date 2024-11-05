import io
import pickle
import struct
from block import Block

class MessageType:
    PROPOSE = "Propose"
    VOTE = "Vote"
    ECHO = "Echo"
    START_PROPOSAL = "Start Proposal"
    FINALIZE = "Finalize"
    TRANSACTION = "Transaction"

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
    
    @staticmethod
    def create_transaction_message(transaction, sender: int):
        """
        Creates a transaction message.

        :param epoch: The epoch for the proposal.
        :param sender: The sender node ID.
        :return: A Message object.
        """
        return Message(MessageType.TRANSACTION, transaction, sender)

    def serialize(self):
            # Serialize the Message object with pickle
            message_data = pickle.dumps(self)
            # Prefix with the length of the serialized data
            length_prefix = struct.pack('!I', len(message_data))  # Network byte order (big-endian)
            return length_prefix + message_data

    @staticmethod
    def deserialize_from_socket(sock):
        """
        Deserializes bytes from a socket back into a Message object.

        :param sock: The socket to read data from.
        :return: A Message object, or None if deserialization fails.
        """
        try:
            # Read the length prefix to know how many bytes to expect
            length_data = sock.recv(4)  # First 4 bytes for length
            if not length_data:
                print("Failed to receive length prefix.")
                return None

            message_length = struct.unpack('!I', length_data)[0]
            
            # Read the entire message based on the length
            data = b""
            while len(data) < message_length:
                packet = sock.recv(message_length - len(data))
                if not packet:
                    print("Incomplete message received.")
                    return None
                data += packet

            # Deserialize the complete message
            return Message.deserialize_from_bytes(data)
        except (pickle.PickleError, AttributeError, struct.error) as e:
            print(f"Deserialization error: {e}")
            return None
        
    @staticmethod
    def deserialize_from_bytes(data):
        """
        Deserializes a byte array back into a Message object.
        
        :param data: The byte data to deserialize.
        :return: A Message object, or None if deserialization fails.
        """
        try:
            with io.BytesIO(data) as byte_stream:
                return pickle.load(byte_stream)
        except (pickle.PickleError, AttributeError) as e:
            print(f"Deserialization error: {e}")
            return None
