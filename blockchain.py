import hashlib
import random
import pickle
from transaction import Transaction

class Blockchain:
    def __init__(self):
        """
        Initializes a new Blockchain object.
        """
        self.chain = []  # List to store the blockchain
        self.pending_transactions = []  # List to store transactions waiting to be included in a block
        self.create_genesis_block()  # Create the first block in the chain (genesis block)
        self.confusion_start = None  # Epoch after which confusion starts
        self.confusion_duration = None  # Duration of the confusion in epochs
        self.confused_mode = False  # Flag to indicate if we are in confused mode

    def create_genesis_block(self):
        """
        Generates the genesis block and appends it to the chain.
        """
        genesis_block = Block(0, [], "0")  # First block, hash of previous block is "0"
        self.chain.append(genesis_block)

    def create_block(self, epoch: int):
        """
        Creates a new block containing all pending transactions and appends it to the blockchain.
        
        :param epoch: The epoch number of the block.
        """
        if len(self.pending_transactions) == 0:
            return None  # No transactions to include in the block

        previous_block = self.chain[-1]
        previous_hash = previous_block.calculate_hash()
        new_block = Block(epoch, self.pending_transactions, previous_hash)
        self.chain.append(new_block)
        self.pending_transactions = []  # Clear the pending transactions
        return new_block

    def add_transaction(self, transaction: Transaction):
        """
        Adds a new transaction to the list of pending transactions.
        
        :param transaction: The transaction to be added.
        """
        if self.validate_transaction(transaction):
            self.pending_transactions.append(transaction)
        else:
            raise ValueError("Invalid transaction")

    def validate_transaction(self, transaction: Transaction) -> bool:
        """
        Validates a transaction. Currently, always returns True.
        
        :param transaction: The transaction to validate.
        :return: Whether the transaction is valid.
        """
        # TODO: Implement transaction validation logic
        return True

    def get_chain(self):
        """
        Returns the current state of the blockchain.
        
        :return: List representing the blockchain.
        """
        return self.chain

    def enable_confusion(self, confusion_start: int, confusion_duration: int):
        """
        Enables a period of confusion to simulate forks.
        
        :param confusion_start: The epoch after which the confusion starts.
        :param confusion_duration: The duration of the confusion in epochs.
        """
        self.confusion_start = confusion_start
        self.confusion_duration = confusion_duration
        self.confused_mode = True

    def should_process_message(self, current_epoch: int) -> bool:
        """
        Determines if messages should be processed based on the current epoch and confusion settings.
        
        :param current_epoch: The current epoch number.
        :return: Whether the message should be processed.
        """
        if not self.confused_mode:
            return True
        if current_epoch < self.confusion_start or current_epoch >= (self.confusion_start + self.confusion_duration):
            return True
        return False

    def save_state(self, filename: str):
        """
        Saves the current state of the blockchain to a file.
        
        :param filename: The name of the file to save the state.
        """
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load_state(filename: str):
        """
        Loads the blockchain state from a file.
        
        :param filename: The name of the file from which to load the state.
        :return: A Blockchain object loaded from the file.
        """
        with open(filename, 'rb') as f:
            return pickle.load(f)


class Block:
    def __init__(self, epoch: int, transactions: list[Transaction], previous_hash: str):
        """
        Initializes a new Block object.
        
        :param epoch: The epoch number the block was generated.
        :param transactions: The list of transactions included in this block.
        :param previous_hash: The hash of the previous block in the chain.
        """
        self.epoch = epoch
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculates the hash of the block based on its content.
        
        :return: The SHA-256 hash of the block.
        """
        block_string = f"{self.epoch}{self.previous_hash}{self.transactions}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int):
        """
        Mines the block by finding a hash with a specified number of leading zeroes.
        
        :param difficulty: The difficulty level of mining, represented by the number of leading zeroes.
        """
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()


if __name__ == "__main__":
    # Example of creating a blockchain and adding transactions with confusion enabled for Phase 2
    blockchain = Blockchain()

    # Enabling confusion to simulate forks
    blockchain.enable_confusion(confusion_start=2, confusion_duration=3)

    # Creating some sample transactions
    transaction1 = Transaction(sender=1, receiver=2, tx_id=1, amount=100.0)
    transaction2 = Transaction(sender=2, receiver=3, tx_id=2, amount=50.0)

    # Adding transactions to the blockchain
    blockchain.add_transaction(transaction1)
    blockchain.add_transaction(transaction2)

    # Creating and mining a new block
    current_epoch = 1
    if blockchain.should_process_message(current_epoch):
        new_block = blockchain.create_block(epoch=current_epoch)
        if new_block:
            new_block.mine_block(difficulty=2)
            blockchain.save_state("blockchain_state.pkl")
            print(f"Block mined with hash: {new_block.hash}")

    # Printing the entire blockchain
    for block in blockchain.get_chain():
        print(f"Block Epoch: {block.epoch}, Hash: {block.hash}, Previous Hash: {block.previous_hash}")