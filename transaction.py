import random
import time


class Transaction:
    def __init__(self, sender: int, receiver: int, tx_id: int, amount: float):
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

    @staticmethod
    def generate_transaction(sender: int, receiver: int, amount: float):
        """
        Generates a new transaction with a unique transaction id.

        :param sender: The sender of the transaction.
        :param receiver: The receiver of the transaction.
        :param amount: The amount to be transferred.
        :return: A Transaction object.
        """
        # Create a unique transaction ID
        unique_id = int(time.time() * 1000) + random.randint(1000, 9999)
        return Transaction(sender, receiver, unique_id, amount)