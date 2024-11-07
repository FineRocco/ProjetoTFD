class Transaction:
    def __init__(self, sender: int, receiver: int, tx_id: int, amount: int):
        """
        Initializes a Transaction object.
        
        :param sender: The sender of the transaction.
        :param receiver: The receiver of the transaction.
        :param tx_id: A unique transaction id.
        :param amount: The amount to be transferred.
        """
        self.sender = sender
        self.receiver = receiver
        self.tx_id = tx_id
        self.amount = amount

