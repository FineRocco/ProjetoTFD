import hashlib
import time
from transaction import Transaction

class Block:
    def __init__(self, epoch, previous_hash: bytes, transactions: list[Transaction]):
        """
        Initializes a Block object with the given epoch, previous hash, and transactions.
        
        :param epoch: The epoch number the block is proposed in.
        :param previous_hash: The SHA1 hash (in bytes) of the previous block.
        :param transactions: The list of transactions in this block.
        """
        self.epoch = epoch
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.length = len(transactions)  # Set the length of transactions in the block
        self.timestamp = time.time()
        self.hash = self.compute_hash()
        self.votes = 0  # Initialize vote count to 0

    def compute_hash(self):
        """
        Computes the SHA1 hash of the block using the epoch, previous hash, transactions, and timestamp.
        """
        transactions_str = ''.join([f'{tx.sender}-{tx.receiver}-{tx.tx_id}-{tx.amount}' for tx in self.transactions])
        block_data = f'{self.epoch}{self.previous_hash.hex()}{transactions_str}{self.timestamp}'
        return hashlib.sha1(block_data.encode()).digest()  # Return hash as bytes (SHA1)

    def __repr__(self):
        return f"Block(epoch={self.epoch}, hash={self.hash.hex()}, length={self.length}, votes={self.votes})"
