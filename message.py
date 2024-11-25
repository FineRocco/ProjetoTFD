# message.py
import json
from block import Block

class MessageType:
    """
    Defines constants for the various message types exchanged between nodes in the network.
    """
    PROPOSE = "PROPOSE"
    VOTE = "VOTE"
    ECHO = "ECHO"

class Message:
    """
    Represents a message exchanged between nodes in the network.
    """

    def __init__(self, message_type, content, sender=None):
        self.type = message_type
        self.content = content
        self.sender = sender

    def serialize(self):
        if isinstance(self.content, Block):
            content = self.content.to_dict()
        elif isinstance(self.content, Message):
            content = self.content.serialize().decode('utf-8')  # ECHO contains a serialized message
        else:
            content = self.content

        return json.dumps({
            'type': self.type,
            'content': content,
            'sender': self.sender,
        }).encode('utf-8')

    @staticmethod
    def deserialize(data):
        try:
            obj = json.loads(data.decode('utf-8'))
            msg_type = obj.get('type')
            content = obj.get('content')
            sender = obj.get('sender', None)

            if not msg_type:
                print("Message type missing or invalid.")
                return None

            # Handle specific message types
            if msg_type in [MessageType.PROPOSE, MessageType.VOTE]:
                if isinstance(content, dict):
                    content = Block.from_dict(content)
                else:
                    print(f"Invalid block content: {content}")
                    return None
            elif msg_type == MessageType.ECHO:
                # Content is a serialized message
                content_data = content.encode('utf-8')
                content = Message.deserialize(content_data)
                if not content:
                    print("Failed to deserialize ECHO content.")
                    return None
            else:
                print(f"Unknown message type: {msg_type}")
                return None

            return Message(msg_type, content, sender)
        except Exception as e:
            print(f"Error during deserialization: {e}")
            return None

    @staticmethod
    def create_propose_message(block, sender):
        return Message(MessageType.PROPOSE, block, sender)

    @staticmethod
    def create_vote_message(block, sender):
        # For VOTE message, the Block's Transactions field should be empty
        block_copy = Block(block.epoch, block.previous_hash, {}, block.length)
        block_copy.hash = block.hash  # Preserve the hash
        return Message(MessageType.VOTE, block_copy, sender)

    @staticmethod
    def create_echo_message(message, sender):
        return Message(MessageType.ECHO, message, sender)
