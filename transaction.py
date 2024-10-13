class Transaction:
    def __init__(self, sender, receiver, transaction_id, amount):
        self._sender = sender           
        self._receiver = receiver          
        self._transaction_id = transaction_id                
        self._amount = amount              
    
    def __repr__(self):
        return (f"Transaction(sender={self.sender}, receiver={self.receiver}, "
                f"transaction_id={self.transaction_id}, amount={self.amount})")
    
    def is_valid(self):
        return (self.receiver != self.sender) & (self.amount > 0)

    @property
    def sender(self):
        return self._sender

    @sender.setter
    def sender(self, value):
        self._sender = value

    @property
    def receiver(self):
        return self._receiver

    @receiver.setter
    def receiver(self, value):
        self._receiver = value

    @property
    def transaction_id(self):
        return self._transaction_id

    @transaction_id.setter
    def transaction_id(self, value):
        self._transaction_id = value

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = value