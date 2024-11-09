class Transaction:
    def __init__(self, tx_id, sender, receiver, amount):
        self.tx_id = tx_id
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
    
    def to_dict(self):
        return {
            'tx_id': self.tx_id,
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount
        }
    
    @staticmethod
    def from_dict(data):
        return Transaction(
            tx_id=data['tx_id'],
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount']
        )
