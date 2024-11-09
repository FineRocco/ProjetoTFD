import hashlib

from transaction import Transaction

class Block:
    def __init__(self, epoch, previous_hash, transactions):
        self.epoch = epoch
        self.previous_hash = previous_hash  # Should be bytes
        self.transactions = transactions    # List of Transaction objects
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        # Create a string representation of the block's contents
        block_string = f"{self.epoch}{self.previous_hash.hex()}{[tx.tx_id for tx in self.transactions]}"
        return hashlib.sha1(block_string.encode('utf-8')).digest()
    
    def to_dict(self):
        return {
            'epoch': self.epoch,
            'previous_hash': self.previous_hash.hex(),
            'transactions': [tx.to_dict() for tx in self.transactions],
            'hash': self.hash.hex()
        }
    
    @staticmethod
    def from_dict(data):
        epoch = data['epoch']
        previous_hash = bytes.fromhex(data['previous_hash'])
        transactions = [Transaction.from_dict(tx) for tx in data['transactions']]
        block = Block(epoch, previous_hash, transactions)
        block.hash = bytes.fromhex(data['hash'])  # Override the hash to match the received block
        return block
