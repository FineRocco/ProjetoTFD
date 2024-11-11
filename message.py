import json
from block import Block
from transaction import Transaction

class MessageType:
    """
    Defines constants for the various message types exchanged between nodes in the network.
    """
    START_PROPOSAL = "START_PROPOSAL"
    PROPOSE = "PROPOSE"
    VOTE = "VOTE"
    ECHO_NOTARIZE = "ECHO_NOTARIZE"
    TRANSACTION = "TRANSACTION"
    ECHO_TRANSACTION = "ECHO_TRANSACTION"
    DISPLAY_BLOCKCHAIN = "DISPLAY_BLOCKCHAIN"

class Message:
    """
    Represents a message exchanged between nodes in the network.
    
    Attributes:
    - type (str): The type of the message (e.g., PROPOSE, VOTE).
    - content (various): The content of the message, varies based on the message type.
    - sender (int): ID of the sending node.
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
            content = self.content.to_dict()
        elif isinstance(self.content, Transaction):
            content = self.content.to_dict()
        elif isinstance(self.content, dict):
            content = self.content  
        else:
            content = self.content  
        
        return json.dumps({
            'type': self.type,
            'content': content,
            'sender': self.sender,
        }).encode('utf-8')
    
    @staticmethod
    def deserialize_from_socket(conn, blockchain_tx_ids, notarized_tx_ids):
        """
        Deserializes a message received from a socket.

        Parameters:
        - conn (socket): The socket connection from which data is received.
        - blockchain_tx_ids (set): Set of transaction IDs already included in the blockchain.
        - notarized_tx_ids (set): Set of transaction IDs already notarized.

        Returns:
        - Message: A Message object or None if deserialization fails.
        """
        try:
            data = conn.recv(4096)  
            if not data:
                print("No data received from socket.")
                return None
            obj = json.loads(data.decode('utf-8'))
            msg_type = obj['type']
            content = obj['content']
            sender = obj.get('sender', None)
    
            if msg_type in [MessageType.PROPOSE, MessageType.ECHO_NOTARIZE, MessageType.VOTE]:
                content = Block.from_dict(content)
            elif msg_type in [MessageType.TRANSACTION, MessageType.ECHO_TRANSACTION]:
                transaction_data = content.get('transaction')
                epoch = content.get('epoch')
                transaction = Transaction.from_dict(transaction_data)
                content = {'transaction': transaction, 'epoch': epoch}
            elif msg_type == MessageType.START_PROPOSAL:
                content = int(content)
            elif msg_type == MessageType.DISPLAY_BLOCKCHAIN:
                content = None  
            else:
                print(f"Unknown message type: {msg_type}")
                return None
    
            if msg_type in [MessageType.TRANSACTION, MessageType.ECHO_TRANSACTION]:
                tx_id = content['transaction'].tx_id
                if tx_id in blockchain_tx_ids:
                    print(f"Transaction {tx_id} already included in blockchain. Ignoring.")
                    return None
                if tx_id in notarized_tx_ids:
                    print(f"Transaction {tx_id} already notarized. Ignoring.")
                    return None
    
            return Message(msg_type, content, sender)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"Error during deserialization from socket: {e}")
            return None
    
    @staticmethod
    def create_start_proposal_message(epoch, sender):
        """
        Creates a START_PROPOSAL message.

        Parameters:
        - epoch (int): The epoch for which the proposal is being started.
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type START_PROPOSAL.
        """
        return Message(MessageType.START_PROPOSAL, epoch, sender)
    
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
    def create_echo_notarize_message(block, sender):
        """
        Creates an ECHO_NOTARIZE message.

        Parameters:
        - block (Block): The block being notarized.
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type ECHO_NOTARIZE.
        """
        return Message(MessageType.ECHO_NOTARIZE, block, sender)
    
    @staticmethod
    def create_transaction_message(transaction, epoch, sender):
        """
        Creates a TRANSACTION message.

        Parameters:
        - transaction (Transaction): The transaction to be sent.
        - epoch (int): The epoch during which the transaction is created.
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type TRANSACTION.
        """
        return Message(MessageType.TRANSACTION, {'transaction': transaction.to_dict(), 'epoch': epoch}, sender)
    
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
    def create_display_blockchain_message(sender):
        """
        Creates a DISPLAY_BLOCKCHAIN message.

        Parameters:
        - sender (int): The ID of the sending node.

        Returns:
        - Message: A Message object of type DISPLAY_BLOCKCHAIN.
        """
        return Message(MessageType.DISPLAY_BLOCKCHAIN, None, sender)
