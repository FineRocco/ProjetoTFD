import hashlib
import time
from transaction import Transaction

class Block:
    """
    Represents a block in the blockchain, which contains a list of transactions, 
    a link to the previous block, and metadata about the block itself.

    Attributes:
        epoch (int): The epoch number in which the block is proposed.
        previous_hash (bytes): SHA1 hash of the previous block in the chain.
        transactions (list[Transaction]): A list of Transaction objects included in this block.
        length (int): The number of transactions in the block.
        timestamp (float): The creation timestamp of the block.
        hash (bytes): SHA1 hash of the block’s data for unique identification.
        votes (int): The vote count for the block (used in the consensus process).
    """

    def __init__(self, epoch, previous_hash: bytes, transactions: list[Transaction]):
        """
        Initializes a Block object with the given epoch, previous hash, and transactions.

        :param epoch: The epoch number the block is proposed in.
        :param previous_hash: The SHA1 hash (in bytes) of the previous block.
        :param transactions: A list of Transaction objects to include in the block.
        """
        self.epoch = epoch
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.length = len(transactions)  # Number of transactions in the block
        self.timestamp = time.time()  # Timestamp when the block was created
        self.hash = self.compute_hash()  # Compute the block's unique hash
        self.votes = 0  # Initialize vote count to zero

    def compute_hash(self):
        """
        Computes the SHA1 hash of the block's data, including the epoch, previous hash,
        transactions, and timestamp, to uniquely identify the block.

        :return: The SHA1 hash of the block as a byte string.
        """
        transactions_str = ''.join(
            [f'{tx.sender}-{tx.receiver}-{tx.tx_id}-{tx.amount}' for tx in self.transactions]
        )
        block_data = f'{self.epoch}{self.previous_hash.hex()}{transactions_str}{self.timestamp}'
        return hashlib.sha1(block_data.encode()).digest()  # Compute and return SHA1 hash as bytes

    def __repr__(self):
        """
        Provides a string representation of the block, showing key attributes 
        such as epoch, hash, number of transactions, and vote count.

        :return: A string representation of the Block object.
        """
        return f"Block(epoch={self.epoch}, hash={self.hash.hex()}, length={self.length}, votes={self.votes})"
