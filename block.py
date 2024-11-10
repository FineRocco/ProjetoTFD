# block.py

import hashlib
from transaction import Transaction

class Block:
    """
    Represents a block in the Blockchain.
    """
    
    def __init__(self, epoch, previous_hash, transactions):
        """
        :param epoch: int - Número do epoch.
        :param previous_hash: bytes - Hash do bloco anterior.
        :param transactions: dict - Dicionário com tx_id como chave e Transaction como valor.
        """
        self.epoch = epoch
        self.previous_hash = previous_hash  # Deve ser bytes
        self.transactions = transactions    # Dicionário: chave=tx_id, valor=Transaction
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """
        Calcula a hash do bloco com base no epoch, hash anterior e tx_ids das transações.
        """
        block_string = f"{self.epoch}{self.previous_hash.hex()}{sorted(self.transactions.keys())}"
        return hashlib.sha1(block_string.encode('utf-8')).digest()
    
    def to_dict(self):
        """
        Serializa o bloco para um dicionário.
        """
        return {
            'epoch': self.epoch,
            'previous_hash': self.previous_hash.hex(),
            'transactions': [tx.to_dict() for tx in self.transactions.values()],
            'hash': self.hash.hex()
        }
    
    @staticmethod
    def from_dict(data):
        """
        Desserializa um bloco a partir de um dicionário.
        """
        epoch = data['epoch']
        previous_hash = bytes.fromhex(data['previous_hash'])
        transactions = {int(tx['tx_id']): Transaction.from_dict(tx) for tx in data['transactions']}
        block = Block(epoch, previous_hash, transactions)
        block.hash = bytes.fromhex(data['hash'])  # Substitui a hash para corresponder ao bloco recebido
        return block
