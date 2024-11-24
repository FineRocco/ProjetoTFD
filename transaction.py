class Transaction:
    """
    Represents a blockchain transaction.
    
    Attributes:
    - tx_id (int): The unique identifier for the transaction.
    - sender (str): The ID or name of the sender in the transaction.
    - receiver (str): The ID or name of the receiver in the transaction.
    - amount (float/int): The amount being transferred in the transaction.
    """
    
    def __init__(self, tx_id, sender, receiver, amount):
        """
        Initializes a new Transaction object with a unique ID, sender, receiver, and amount.
        
        Parameters:
        - tx_id (int): The unique identifier for the transaction.
        - sender (str): The sender’s identifier.
        - receiver (str): The receiver’s identifier.
        - amount (float/int): The amount of value being transferred.
        """
        self.tx_id = int(tx_id)  
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
    
    def to_dict(self):
        """
        Serializes the transaction to a dictionary format.
        
        Returns:
        - dict: A dictionary representation of the transaction, containing the transaction ID, sender, receiver, and amount.
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
        
        Parameters:
        - data (dict): A dictionary containing `tx_id`, `sender`, `receiver`, and `amount` fields.

        Returns:
        - Transaction: A Transaction object constructed from the dictionary data.
        """
        return Transaction(
            tx_id=int(data['tx_id']),
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount']
        )
