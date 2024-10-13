from ProjetoTFD import block


class Blockchain:
    def __init__(self):
        self.chain = []  # List to hold blocks
        self.notarized_blocks = []  # List of notarized blocks
        self.finalized_blocks = []  # List of finalized blocks

    def add_block(self, Block: block):
        if self.is_valid_block(block):
            self.chain.append(block)
            print(f"Block {block.length} added to the blockchain.")
        else:
            print(f"Block {block.length} is invalid and cannot be added.")

    def is_valid_block(self, Block: block):
        if not self.chain:  # If the chain is empty, the block is valid
            return True
        last_block = self.chain[-1]
        return last_block.calculate_hash() == block.previous_hash

    def notarize_block(self, Block: block):
        """Add a block to the notarized blocks list."""
        if block not in self.notarized_blocks:
            self.notarized_blocks.append(block)
            print(f"Block {block.length} notarized.")

    def check_blockchain_notarization(self):
        """Check if all blocks in the blockchain are notarized."""
        if all(block in self.notarized_blocks for block in self.chain[1:]):
            print("Blockchain is fully notarized and valid.")
        else:
            print("Blockchain is not fully notarized yet.")

    def finalize(self):
        """Finalize blocks based on notarization and their sequential epochs."""
        if len(self.notarized_blocks) < 3:
            return

        for i in range(len(self.notarized_blocks) - 2):
            block1 = self.notarized_blocks[i]
            block2 = self.notarized_blocks[i + 1]
            block3 = self.notarized_blocks[i + 2]

            if (block1.epoch + 1 == block2.epoch and
                block2.epoch + 1 == block3.epoch):
                self.finalized_blocks.append(block2)
                print(f"Finalized block {block2.length} from epoch {block2.epoch}.")
                return

    def __repr__(self):
        return f"Blockchain with {len(self.chain)} blocks."
