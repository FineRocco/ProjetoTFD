# message.py

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
    """
    Representa uma mensagem a ser trocada entre os nós.
    """
    
    def __init__(self, message_type, content, sender=None):
        """
        :param message_type: str - Tipo da mensagem.
        :param content: Vários - Conteúdo da mensagem, dependendo do tipo.
        :param sender: int - ID do nó remetente.
        """
        self.type = message_type
        self.content = content    
        self.sender = sender      
    
    def serialize(self):
        """
        Serializa a mensagem para bytes para envio via rede.
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
        Desserializa uma mensagem recebida de um socket.
        
        :param conn: socket - Conexão de onde a mensagem foi recebida.
        :param blockchain_tx_ids: set - Conjunto de tx_ids já incluídas na blockchain.
        :param notarized_tx_ids: set - Conjunto de tx_ids já notarizadas.
        :return: Message ou None
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
    def create_transaction_message(transaction, epoch, sender):
        return Message(MessageType.TRANSACTION, {'transaction': transaction.to_dict(), 'epoch': epoch}, sender)
    
    @staticmethod
    def create_echo_transaction_message(transaction, epoch, sender):
        return Message(MessageType.ECHO_TRANSACTION, {'transaction': transaction.to_dict(), 'epoch': epoch}, sender)
    
    @staticmethod
    def create_display_blockchain_message(sender):
        return Message(MessageType.DISPLAY_BLOCKCHAIN, None, sender)
