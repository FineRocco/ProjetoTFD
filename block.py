# block.py

import hashlib
import time
from transaction import Transaction

class Block:
    def __init__(self, epoch, previous_hash, transactions: list[Transaction]):
        """
        Initializes a Block object.
        
        :param epoch: The epoch number the block is proposed in.
        :param previous_hash: The hash of the previous block.
        :param transactions: The list of transactions in this block.
        """
        self.epoch = epoch
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = time.time()
        self.hash = self.compute_hash()

    def compute_hash(self):
        """
        Computes the SHA-256 hash of the block.
        """
        transactions_str = ''.join([f'{tx.sender}-{tx.receiver}-{tx.tx_id}-{tx.amount}' for tx in self.transactions])
        block_data = f'{self.epoch}{self.previous_hash}{transactions_str}{self.timestamp}'
        return hashlib.sha256(block_data.encode()).hexdigest()

    def generate_block(self, epoch: int, transactions: list[Transaction], previous_hash: bytes):
        """
        Generates a new block with the given transactions.

        :param epoch: The epoch number.
        :param transactions: The list of transactions to include in the block.
        :param previous_hash: The hash of the previous block.
        :return: A Block object.
        """
        return Block(epoch=epoch, previous_hash=previous_hash, transactions=transactions)

