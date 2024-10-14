from hashlib import sha256
from ProjetoTFD import block  # Assuming this is your Block class

class Blockchain:
    def __init__(self, initial_block):
        self.blocks = [initial_block]

    def calculate_block_hash(self, block):
        """Calculates the SHA-256 hash of a block."""
        block_data = f"{block.previous_hash}{block.epoch}{block.transactions}"
        return sha256(block_data.encode()).hexdigest()

    def check_block_validity(self, block, previous_block):
        """A block is considered valid if its parent hash is equal to the hash of the
        previous block and their epochs are incremental, excluding genesis."""
        if block.previous_hash == "0":  # Genesis block doesn't have a previous hash
            raise AssertionError("Genesis block provided, not valid for regular block.")
        
        expected_hash = self.calculate_block_hash(previous_block)
        assert block.previous_hash == expected_hash, "Invalid block hash."
        assert block.epoch > previous_block.epoch, "Epochs are not incremental."

    def check_chain_validity(self):
        """A blockchain is considered valid when every block is valid based on the check_block_validity method."""
        for index, block in enumerate(self.blocks[1:], start=1):
            self.check_block_validity(block, self.blocks[index - 1])

    def add_block(self, block):
        """Add a block if it's valid."""
        if len(self.blocks) == 0 or self.check_block_validity(block, self.blocks[-1]):
            self.blocks.append(block)
        else:
            raise Exception("Invalid block")

    def is_notarized(self):
        """Blockchain notarization check. All blocks must be notarized."""
        return all(block.notarized for block in self.blocks)  # Using list comprehension for clarity

    def notarize_block(self, block):
        """Mark the block as notarized."""
        block.notarized = True

    def finalize(self):
        """Finalize the blocks in order."""
        for block in self.blocks:
            if block.notarized and not block.finalized:
                block.finalized = True
                print(f"Block {block.length} finalized in epoch {block.epoch}.")
