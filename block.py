import hashlib
import json
import time
from transaction import Transaction
from message import Message
from node import Node

class Block:
    def __init__(self, hash: bytes, epoch: int, length: int, transactions: list[Transaction]):
        """
        Initializes a Block object.

        :param hash: The SHA1 hash of the previous block.
        :param epoch: The epoch number the block was generated.
        :param length: The position of the block in the blockchain.
        :param transactions: The list of transactions in this block.
        """
        self.hash = hash
        self.epoch = epoch
        self.length = length
        self.transactions = transactions
        self.votes = set()  # Set to store unique voter IDs

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
            'previous_hash': self.hash.hex(),
            'votes': list(self.votes)  # Convert set to list for serialization
        }
        return json.dumps(block_data, sort_keys=True)

    @classmethod
    def generate_block(cls, epoch: int, transactions: list[Transaction], previous_block: 'Block') -> 'Block':
        """
        Generates a new block with the given transactions based on the previous block.

        :param epoch: The epoch number.
        :param transactions: The list of transactions to include in the block.
        :param previous_block: The previous block in the chain.
        :return: A Block object with a computed hash.
        """
        new_length = previous_block.length + 1
        new_block = cls(
            hash=previous_block.hash,
            epoch=epoch,
            length=new_length,
            transactions=transactions
        )
        serialized_block = new_block.serialize_block()
        new_block.hash = cls.compute_hash(serialized_block)
        return new_block

    def add_vote(self, voter_id: int):
        """
        Adds a vote from a node to this block.

        :param voter_id: The ID of the node casting the vote.
        """
        self.votes.add(voter_id)

    def is_notarized(self, total_nodes: int) -> bool:
        """
        Checks if the block has enough votes to be notarized.

        :param total_nodes: The total number of nodes in the network.
        :return: True if the block is notarized, False otherwise.
        """
        return len(self.votes) > total_nodes / 2

    def __repr__(self):
        return (f"Block(epoch={self.epoch}, hash={self.hash.hex()}, length={self.length}, "
                f"votes={len(self.votes)}, transactions={len(self.transactions)})")
