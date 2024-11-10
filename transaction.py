# transaction.py

class Transaction:
    """
    Represents a blockchain transaction.
    """
    
    def __init__(self, tx_id, sender, receiver, amount):
        self.tx_id = int(tx_id)  
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
    
    def to_dict(self):
        """
        Serializa a transação para um dicionário.
        """
        return {
            'tx_id': self.tx_id,
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount
        }
    
    @staticmethod
    def from_dict(data):
        """
        Desserializa uma transação a partir de um dicionário.
        """
        return Transaction(
            tx_id=int(data['tx_id']),
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount']
        )
