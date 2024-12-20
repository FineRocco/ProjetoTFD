import json
from block import Block
from transaction import Transaction

class MessageType:
    """
    Defines constants for the various message types exchanged between nodes in the network.
    """
    PROPOSE = "PROPOSE"  # Proposing a new block
    VOTE = "VOTE"  # Voting for a proposed block
    ECHO_TRANSACTION = "ECHO_TRANSACTION"  # Broadcasting a transaction
    QUERY_MISSING_BLOCKS = "QUERY_MISSING_BLOCKS"  # Request for missing blocks
    RESPONSE_MISSING_BLOCKS = "RESPONSE_MISSING_BLOCKS"  # Response with missing blocks

class Message:
    """
    Represents a message exchanged between nodes in the network.
    
    Attributes:
    - type (str): The type of the message (e.g., PROPOSE, VOTE).
    - content (varies): The content of the message, which varies based on the type.
    - sender (int): The ID of the sending node.
    """

    def __init__(self, message_type, content, sender=None):
        """
        Initializes a new Message object.

        Parameters:
        - message_type (str): The type of message.
        - content (varies): The content of the message, depending on the type.
        - sender (int, optional): The ID of the sender node.
        """
        self.type = message_type
        self.content = content
        self.sender = sender      
    
    def serialize(self):
            """
            Serializes the message to bytes for network transmission.

            Returns:
            - bytes: The serialized message in JSON format.
            """
            if isinstance(self.content, Block):
                content = self.content.to_dict()  # Convert block to a dictionary
            elif isinstance(self.content, Transaction):
                content = self.content.to_dict()  # Convert transaction to a dictionary
            elif isinstance(self.content, dict):
                if self.type == MessageType.RESPONSE_MISSING_BLOCKS:
                    # Special handling for missing blocks response
                    content = {
                        "missing_blocks": [
                            block.to_dict() if isinstance(block, Block) else block
                            for block in self.content.get("missing_blocks", [])
                        ]
                    }
                else:
                    content = self.content
            else:
                content = self.content  # Other content types are serialized directly

            return json.dumps({
                'type': self.type,
                'content': content,
                'sender': self.sender,
            }).encode('utf-8')
    
    @staticmethod
    def deserialize_from_socket(conn, blockchain_tx_ids=None, notarized_tx_ids=None):
        """
        Deserializes a message received from a socket.

        Parameters:
        - conn (socket): The socket connection from which data is received.
        - blockchain_tx_ids (set, optional): Set of transaction IDs already included in the blockchain.
        - notarized_tx_ids (set, optional): Set of transaction IDs already notarized.

        Returns:
        - Message: A Message object or None if deserialization fails.
        """
        try:
            data = conn.recv(4096)  # Read up to 4 KB of data
            if not data:
                print("No data received from socket.")
                return None

            obj = json.loads(data.decode('utf-8'))  # Decode JSON into a Python object
            msg_type = obj.get('type')
            content = obj.get('content')
            sender = obj.get('sender', None)

            if not msg_type:
                print("Message type missing or invalid.")
                return None

            # Handle specific message types
            if msg_type in [MessageType.PROPOSE, MessageType.VOTE]:
                if isinstance(content, dict):
                    content = Block.from_dict(content)  # Convert content back to a Block
                else:
                    print(f"Invalid block content: {content}")
                    return None
            elif msg_type == MessageType.ECHO_TRANSACTION:
                if isinstance(content, dict):
                    transaction_data = content.get('transaction')
                    epoch = content.get('epoch')
                    if transaction_data and epoch is not None:
                        transaction = Transaction.from_dict(transaction_data)
                        content = {'transaction': transaction, 'epoch': epoch}
                    else:
                        print(f"Invalid transaction content: {content}")
                        return None
                else:
                    print(f"Invalid content format for ECHO_TRANSACTION: {content}")
                    return None
            elif msg_type == MessageType.RESPONSE_MISSING_BLOCKS:
                if isinstance(content, dict) and "missing_blocks" in content:
                    content["missing_blocks"] = [
                        Block.from_dict(block_data) for block_data in content["missing_blocks"]
                    ]
                else:
                    print(f"Invalid content format for RESPONSE_MISSING_BLOCKS: {content}")
                    return None
            elif msg_type in [MessageType.QUERY_MISSING_BLOCKS]:
                # QUERY messages typically have simpler content
                pass
            else:
                print(f"Unknown message type: {msg_type}")
                return None

            return Message(msg_type, content, sender)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
    
    @staticmethod
    def create_propose_message(block, sender):
        """
        Creates a PROPOSE message.

        Parameters:
        - block (Block): The block being proposed.
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type PROPOSE.
        """
        return Message(MessageType.PROPOSE, block, sender)

    @staticmethod
    def create_vote_message(block, sender):
        """
        Creates a VOTE message.

        Parameters:
        - block (Block): The block being voted on.
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type VOTE.
        """
        return Message(MessageType.VOTE, block, sender)

    @staticmethod
    def create_echo_transaction_message(transaction, epoch, sender):
        """
        Creates an ECHO_TRANSACTION message.

        Parameters:
        - transaction (Transaction): The transaction to be echoed.
        - epoch (int): The epoch during which the transaction is created.
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type ECHO_TRANSACTION.
        """
        return Message(MessageType.ECHO_TRANSACTION, {'transaction': transaction.to_dict(), 'epoch': epoch}, sender)

    @staticmethod
    def create_query_missing_blocks_message(last_epoch, sender):
        """
        Creates a QUERY_MISSING_BLOCKS message.

        Parameters:
        - last_epoch (int): The last known epoch of the requesting node.
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type QUERY_MISSING_BLOCKS.
        """
        return Message(MessageType.QUERY_MISSING_BLOCKS, {"last_epoch": last_epoch}, sender)

    @staticmethod
    def create_response_missing_blocks_message(missing_blocks, sender):
        """
        Creates a RESPONSE_MISSING_BLOCKS message.

        Parameters:
        - missing_blocks (list of Block): The list of missing blocks to send.
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type RESPONSE_MISSING_BLOCKS.
        """
        return Message(MessageType.RESPONSE_MISSING_BLOCKS, {"missing_blocks": [block.to_dict() for block in missing_blocks]}, sender)
