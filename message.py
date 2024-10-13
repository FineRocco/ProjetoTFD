class Message:
    def __init__(self, msg_type, content, sender):
        self.msg_type = msg_type  # (Propose, Vote, Echo)
        self.content = content      
        self.sender = sender
    
    def __repr__(self):
        return (f"Message(type={self.msg_type}, sender={self.sender}, "
                f"content={self.content})")
    
    @property
    def msg_type(self):
        return self._msg_type

    @msg_type.setter
    def msg_type(self, value):
        self._msg_type = value

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    @property
    def sender(self):
        return self._sender

    @sender.setter
    def sender(self, value):
        self._sender = value        
