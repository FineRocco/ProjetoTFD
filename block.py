import hashlib
from transaction import Transaction
import json

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
        return hashlib.sha1(block_data.encode()).digest()

    def serialize_block(self) -> str:
        """
        Serializes the block data into a string format for hashing.

        :return: A string representation of the block data.
        """
        block_data = {
            'epoch': self.epoch,
            'length': self.length,
            'transactions': [tx.__dict__ for tx in self.transactions],
            'previous_hash': self.hash.hex()
        }
        return json.dumps(block_data, sort_keys=True)

    @classmethod
    def generate_block(cls, epoch: int, transactions: list[Transaction], previous_hash: bytes) -> 'Block':
        """
        Generates a new block with the given transactions.

        :param epoch: The epoch number.
        :param transactions: The list of transactions to include in the block.
        :param previous_hash: The hash of the previous block.
        :return: A Block object.
        """
        block_data = cls(hash=previous_hash, epoch=epoch, length=len(transactions), transactions=transactions)
        serialized_block = block_data.serialize_block()
        block_hash = cls.compute_hash(serialized_block)
        block_data.hash = block_hash
        return block_data

