from hashlib import sha256

from ProjetoTFD import block

class Blockchain:
    def __init__(self, initial_block):
        self.blocks = [initial_block]

    def check_block_validity(self, Block: block, previous_block):
        """A block is considered valid when its parent hash is equal to the hash of the
        previous block and their epochs are incremental, excluding genesis.
        Additional validity rules can be applied."""
        assert block.header != "⊥", "Genesis block provided."
        hasher = hash(previous_block)
        assert (
            block.previous_hash == str(hasher) and block.epoch > previous_block.epoch
        ), "Provided block is invalid."

    def check_chain_validity(self):
        """A blockchain is considered valid, when every block is valid, based on check_block_validity method."""
        for index, block in enumerate(self.blocks[1:], start=1):
            self.check_block_validity(block, self.blocks[index - 1])

    def add_block(self, Block: block):
        """Insertion of a valid block."""
        self.check_block_validity(block, self.blocks[-1])
        self.blocks.append(block)

    def is_notarized(self):
        """Blockchain notarization check."""
        for  block in self.blocks:
            if not block.notarized:
                return False
        return True