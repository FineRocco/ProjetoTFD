import io
import pickle
import struct
from block import Block

class MessageType:
    """
    Enum-like class representing the types of messages exchanged in the Streamlet protocol.

    Attributes:
        PROPOSE (str): Message for proposing a new block.
        VOTE (str): Message for voting on a proposed block.
        ECHO_NOTARIZE (str): Message for echoing a block's notarization.
        ECHO_TRANSACTION (str): Message for echoing a transaction.
        START_PROPOSAL (str): Message for starting a proposal in an epoch.
        FINALIZE (str): Message for finalizing a block.
        TRANSACTION (str): Message containing a new transaction.
        DISPLAY_BLOCKCHAIN (str): Command to display the blockchain.
    """
    PROPOSE = "Propose"
    VOTE = "Vote"
    ECHO_NOTARIZE = "Echo Notarize"
    ECHO_TRANSACTION = "Echo Transaction"
    START_PROPOSAL = "Start Proposal"
    FINALIZE = "Finalize"
    TRANSACTION = "Transaction"
    DISPLAY_BLOCKCHAIN = "Display Blockchain"

class Message:
    """
    Represents a message used in the Streamlet protocol, with utilities for serialization and deserialization.

    Attributes:
        type (str): The type of the message (from MessageType).
        content (any): The message content (e.g., a Block, epoch number, or transaction).
        sender (int): ID of the sender node.
    """

    def __init__(self, type: str, content, sender: int):
        """
        Initializes a Message object.

        :param type: The type of the message (e.g., Propose, Vote, Echo Notarize).
        :param content: The content of the message (e.g., a Block, epoch number, or transaction).
        :param sender: The ID of the node sending the message.
        """
        self.type = type
        self.content = content
        self.sender = sender

    @staticmethod
    def create_propose_message(block: Block, sender: int):
        """
        Creates a Propose message for a new block.

        :param block: The Block object being proposed.
        :param sender: The ID of the proposing node.
        :return: A Message object of type Propose.
        """
        return Message(MessageType.PROPOSE, block, sender)

    @staticmethod
    def create_vote_message(block: Block, sender: int):
        """
        Creates a Vote message for a block.

        :param block: The Block object being voted on.
        :param sender: The ID of the voting node.
        :return: A Message object of type Vote with a simplified Block.
        """
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
    def create_echo_notarize_message(message, sender: int):
        """
        Creates an Echo Notarize message for broadcasting notarization info.

        :param message: The content to echo (e.g., a notarized Block).
        :param sender: The ID of the echoing node.
        :return: A Message object of type Echo Notarize.
        """
        return Message(MessageType.ECHO_NOTARIZE, message, sender)
    
    @staticmethod
    def create_echo_transaction_message(message, sender: int):
        """
        Creates an Echo Transaction message to broadcast a new transaction.

        :param message: The Transaction to echo.
        :param sender: The ID of the echoing node.
        :return: A Message object of type Echo Transaction.
        """
        return Message(MessageType.ECHO_TRANSACTION, message, sender)
    
    @staticmethod
    def create_start_proposal_message(epoch: int, sender: int):
        """
        Creates a Start Proposal message for a new epoch.

        :param epoch: The epoch number for the proposal.
        :param sender: The ID of the proposing node.
        :return: A Message object of type Start Proposal.
        """
        return Message(MessageType.START_PROPOSAL, epoch, sender)
    
    @staticmethod
    def create_transaction_message(transaction, sender: int):
        """
        Creates a Transaction message.

        :param transaction: The transaction data to send.
        :param sender: The ID of the node creating the transaction.
        :return: A Message object of type Transaction.
        """
        return Message(MessageType.TRANSACTION, transaction, sender)
    
    @staticmethod
    def create_display_blockchain_message(none, sender: int):
        """
        Creates a Display Blockchain command message.

        :param none: Placeholder parameter (unused).
        :param sender: The ID of the node requesting the display.
        :return: A Message object of type Display Blockchain.
        """
        return Message(MessageType.DISPLAY_BLOCKCHAIN, none, sender)

    def serialize(self):
        """
        Serializes the Message object for transmission over a network.

        :return: The serialized byte data with a length prefix.
        """
        message_data = pickle.dumps(self)
        length_prefix = struct.pack('!I', len(message_data))  # Network byte order (big-endian)
        return length_prefix + message_data

    @staticmethod
    def deserialize_from_socket(sock):
        """
        Deserializes a Message object received from a socket.

        :param sock: The socket to read the serialized data from.
        :return: A Message object, or None if deserialization fails.
        """
        try:
            length_data = sock.recv(4)  # First 4 bytes for length
            if not length_data:
                print("Failed to receive length prefix.")
                return None

            message_length = struct.unpack('!I', length_data)[0]
            
            data = b""
            while len(data) < message_length:
                packet = sock.recv(message_length - len(data))
                if not packet:
                    print("Incomplete message received.")
                    return None
                data += packet

            return Message.deserialize_from_bytes(data)
        except (pickle.PickleError, AttributeError, struct.error) as e:
            print(f"Deserialization error: {e}")
            return None
        
    @staticmethod
    def deserialize_from_bytes(data):
        """
        Deserializes byte data into a Message object.

        :param data: The byte data to deserialize.
        :return: A Message object, or None if deserialization fails.
        """
        try:
            with io.BytesIO(data) as byte_stream:
                return pickle.load(byte_stream)
        except (pickle.PickleError, AttributeError) as e:
            print(f"Deserialization error: {e}")
            return None
