# signals,py - Information and different video streams in the code

import uuid


class Source:
    def __init__(self, name, preferred_out = None):
        self.uuid = uuid.uuid4()
        self.name = name
        self.preferred_out = preferred_out

    def __repr__(self):
        return f"Source({self.name})"
