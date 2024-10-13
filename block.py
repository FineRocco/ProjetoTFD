import hashlib

class Block:
    def __init__(self, previous_hash, epoch, length, transactions):
        self._previous_hash = previous_hash  
        self._epoch = epoch                   
        self._length = length                 
        self._transactions = transactions     

    def calculate_hash(self):
        block_string = f"{self.previous_hash}{self.epoch}{self.length}{self.transactions}"
        return hashlib.sha1(block_string.encode()).hexdigest()

    def __repr__(self):
        return (f"Block(previous_hash={self.previous_hash}, epoch={self.epoch}, "
                f"length={self.length}, transactions={self.transactions})")

    @property
    def previous_hash(self):
        return self._previous_hash

    @previous_hash.setter
    def previous_hash(self, value):
        self._previous_hash = value

    @property
    def epoch(self):
        return self._epoch

    @epoch.setter
    def epoch(self, value):
        self._epoch = value

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    @property
    def transactions(self):
        return self._transactions