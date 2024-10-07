# block.py

import hashlib
from transaction import Transaction

class Block:
    def __init__(self, hash: bytes, epoch: int, length: int, transactions: list[Transaction]):
        """
        Initializes a Block object.

        :param hash: The hash of the previous block.
        :param epoch: The epoch number the block was generated.
        :param length: The length of the blockchain.
        :param transactions: The list of transactions in this block.
        """
        self.hash = hash
        self.epoch = epoch
        self.length = length
        self.transactions = transactions

    @staticmethod
    def compute_hash(block_data: str) -> bytes:
        """
        Computes the SHA-1 hash of the block data.

        :param block_data: The serialized block data to hash.
        :return: The SHA-1 hash of the block.
        """
        # To Do: Implement hash computation logic
        pass

    def serialize_block(self) -> str:
        """
        Serializes the block data into a string format for hashing.

        :return: A string representation of the block data.
        """
        # To Do: Implement block serialization logic
        pass

    def generate_block(self, epoch: int, transactions: list[Transaction], previous_hash: bytes):
        """
        Generates a new block with the given transactions.

        :param epoch: The epoch number.
        :param transactions: The list of transactions to include in the block.
        :param previous_hash: The hash of the previous block.
        :return: A Block object.
        """
        # To Do: Implement block generation logic
        pass
