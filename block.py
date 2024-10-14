import hashlib
import time

class Block:
    def __init__(self, previous_hash, epoch, length, header, transactions):
        self.previous_hash = previous_hash  
        self.epoch = epoch                   
        self.length = length  
        self.header = header               
        self.transactions = transactions     
        self.votes = []
        self.notarized = False
        self.finalized = False
        self.timestamp = time.time()
        
    def calculate_hash(self):
        block_string = f"{self.previous_hash}{self.epoch}{self.length}{self.header}
        {self.transactions}{self.votes}{self.notarized}{self.finalized}{self.timestamp}"
        return hashlib.sha1(block_string.encode()).hexdigest()

    def __repr__(self):
        return (f"Block(previous_hash={self.previous_hash}, epoch={self.epoch}, "
                f"length={self.length}, transactions={self.transactions})")
   
    def __eq__(self, other: 'Block') -> bool:
        return (self.header == other.header and 
                self._previous_hash == other._previous_hash and 
                self.epoch == other.epoch and 
                self.transactions == other.transactions)