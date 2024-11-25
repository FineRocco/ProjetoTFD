# transaction.py
class Transaction:
    """
    Represents a blockchain transaction.
    """

    def __init__(self, tx_id, sender, receiver, amount):
        """
        Initializes a new Transaction object with a unique ID, sender, receiver, and amount.
        """
        self.tx_id = int(tx_id)
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def to_dict(self):
        """
        Serializes the transaction to a dictionary format.
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
        Deserializes a transaction from a dictionary format.
        """
        return Transaction(
            tx_id=int(data['tx_id']),
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount']
        )
