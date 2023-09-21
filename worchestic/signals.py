# signals,py - Information and different video streams in the code

import uuid

class Source:
    def __init__(self, name):
        self.uuid = uuid.uuid4()
        self.name = name
