import json
from block import Block
from transaction import Transaction

class MessageType:
    START_PROPOSAL = "START_PROPOSAL"
    PROPOSE = "PROPOSE"
    VOTE = "VOTE"
    ECHO_NOTARIZE = "ECHO_NOTARIZE"
    TRANSACTION = "TRANSACTION"
    ECHO_TRANSACTION = "ECHO_TRANSACTION"
    DISPLAY_BLOCKCHAIN = "DISPLAY_BLOCKCHAIN"

class Message:
    def __init__(self, message_type, content, sender=None):
        self.type = message_type
        self.content = content  # Can be a Block, Transaction, int, or None
        self.sender = sender    # Sender node ID
    
    def serialize(self):
        return json.dumps({
            'type': self.type,
            'content': self.content.to_dict() if hasattr(self.content, 'to_dict') else self.content,
            'sender': self.sender
        }).encode('utf-8')
    
    @staticmethod
    def deserialize_from_socket(conn):
        try:
            data = conn.recv(4096)
            if not data:
                return None
            message_dict = json.loads(data.decode('utf-8'))
            message_type = message_dict['type']
            content = message_dict['content']
            sender = message_dict.get('sender', None)
    
            # Reconstruct the content object based on message type
            if message_type in [MessageType.PROPOSE, MessageType.VOTE, MessageType.ECHO_NOTARIZE]:
                content = Block.from_dict(content)  # Deserialize as a Block object
            elif message_type in [MessageType.TRANSACTION, MessageType.ECHO_TRANSACTION]:
                content = Transaction.from_dict(content)  # Deserialize as a Transaction object
            elif message_type == MessageType.START_PROPOSAL:
                content = int(content)
            elif message_type == MessageType.DISPLAY_BLOCKCHAIN:
                content = None  # No content needed for display

            return Message(message_type, content, sender)
        except Exception as e:
            print(f"Failed to deserialize message: {e}")
            return None
    
    @staticmethod
    def create_start_proposal_message(epoch, sender):
        return Message(MessageType.START_PROPOSAL, epoch, sender)
    
    @staticmethod
    def create_propose_message(block, sender):
        return Message(MessageType.PROPOSE, block, sender)
    
    @staticmethod
    def create_vote_message(block, sender):
        return Message(MessageType.VOTE, block, sender)
    
    @staticmethod
    def create_echo_notarize_message(block, sender):
        return Message(MessageType.ECHO_NOTARIZE, block, sender)
    
    @staticmethod
    def create_transaction_message(transaction, sender):
        return Message(MessageType.TRANSACTION, transaction, sender)
    
    @staticmethod
    def create_echo_transaction_message(transaction, sender):
        return Message(MessageType.ECHO_TRANSACTION, transaction, sender)
    
    @staticmethod
    def create_display_blockchain_message(sender):
        return Message(MessageType.DISPLAY_BLOCKCHAIN, None, sender)
