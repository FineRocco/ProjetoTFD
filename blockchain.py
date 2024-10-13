from block import Block

class Blockchain:
    def __init__(self):
        self.chain = []  # List to hold blocks

    def add_block(self, block):
        if self.is_valid_block(block):
            self.chain.append(block)
            print(f"Block {block.length} added to the blockchain.")
        else:
            print(f"Block {block.length} is invalid and cannot be added.")

    def is_valid_block(self, block):
        if not self.chain:  # If the chain is empty, the block is valid
            return True
        last_block = self.chain[-1]
        return last_block.calculate_hash() == block.previous_hash

    def __repr__(self):
        return f"Blockchain with {len(self.chain)} blocks."
