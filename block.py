import hashlib
from transaction import Transaction

class Block:
    """
    Represents a block in the Blockchain, storing transactions, the epoch number, length, and a link to the previous block through its hash.
    """
    
    def __init__(self, epoch, previous_hash, transactions, length):
        """
        Initializes a Block object with an epoch number, hash of the previous block, a set of transactions, and the chain length.

        :param epoch: int - The epoch number of the block, indicating its place in the blockchain.
        :param previous_hash: bytes - SHA-1 hash of the previous block in the chain.
        :param transactions: dict - A dictionary where each key is a transaction ID (tx_id) and each value is a Transaction object.
        :param length: int - The length of the chain up to this block.
        """
        self.epoch = epoch
        self.previous_hash = previous_hash  # Should be of type bytes.
        self.transactions = transactions    # Dictionary with transaction ID as key and Transaction as value.
        self.length = length                # Length of the chain up to this block.
        self.hash = self.calculate_hash()   # Hash calculated for this block's data.
    
    def calculate_hash(self):
        """
        Calculates the SHA-1 hash for the block using the length, epoch, previous block hash, and transaction IDs.

        :return: bytes - The SHA-1 hash representing the block.
        """
        block_string = f"{self.length}{self.epoch}{self.previous_hash.hex()}{sorted(self.transactions.keys())}"
        return hashlib.sha1(block_string.encode('utf-8')).digest()
    
    def to_dict(self):
        """
        Serializes the Block object into a dictionary format.

        :return: dict - A dictionary with the block's epoch, previous hash, transactions, length, and current hash.
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

        :param data: dict - A dictionary containing the block's attributes.
        :return: Block - A reconstructed Block object with all attributes.
        """
        epoch = data['epoch']
        previous_hash = bytes.fromhex(data['previous_hash'])
        transactions = {int(tx['tx_id']): Transaction.from_dict(tx) for tx in data['transactions']}
        length = data['length']
        block = Block(epoch, previous_hash, transactions, length)
        block.hash = bytes.fromhex(data['hash'])  # Set the hash to match the received block data
        return block
