# block.py
import hashlib
from transaction import Transaction

class Block:
    """
    Represents a block in the Blockchain, storing transactions, the epoch number, length, and a link to the previous block through its hash.
    """

    def __init__(self, epoch, previous_hash, transactions, length):
        """
        Initializes a Block object with an epoch number, hash of the previous block, a set of transactions, and the chain length.
        """
        self.epoch = epoch
        self.previous_hash = previous_hash  # Should be of type bytes.
        self.transactions = transactions    # Dictionary with transaction ID as key and Transaction as value.
        self.length = length                # Length of the chain up to this block.
        self.hash = self.calculate_hash()   # Hash calculated for this block's data.

    def calculate_hash(self):
        """
        Calculates the SHA-1 hash for the block using the length, epoch, previous block hash, and transaction IDs.
        """
        tx_ids = sorted(self.transactions.keys())
        block_string = f"{self.length}{self.epoch}{self.previous_hash.hex()}{tx_ids}"
        return hashlib.sha1(block_string.encode('utf-8')).digest()

    def to_dict(self):
        """
        Serializes the Block object into a dictionary format.
        """
        return {
            'epoch': self.epoch,
            'previous_hash': self.previous_hash.hex(),
            'transactions': [tx.to_dict() for tx in self.transactions.values()],
            'length': self.length,
            'hash': self.hash.hex()
        }

    @staticmethod
    def from_dict(data):
        """
        Deserializes a dictionary to reconstruct a Block object.
        """
        epoch = data['epoch']
        previous_hash = bytes.fromhex(data['previous_hash'])
        transactions = {int(tx['tx_id']): Transaction.from_dict(tx) for tx in data['transactions']}
        length = data['length']
        block = Block(epoch, previous_hash, transactions, length)
        block.hash = bytes.fromhex(data['hash'])  # Set the hash to match the received block data
        return block
