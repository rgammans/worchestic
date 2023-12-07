# signals,py - Information and different video streams in the code
from typing import Protocol
import uuid


class Source:
    _registry = {}

    def __init__(self, name, preferred_out=None):
        self.uuid = uuid.uuid4()
        self.name = name
        self.preferred_out = preferred_out
        self.register(self)

    def __repr__(self):
        return f"Source({self.name})"

    @classmethod
    def register(kls, self):
        kls._registry[self.uuid] = self

    @classmethod
    def list(kls):
        return kls._registry.values()

    @classmethod
    def reset_registry(kls):
        """Forget all previous;y created monitors.

        mostly useful of ensuring tests are indepedent
        """
        kls._registry = {}

    @classmethod
    def get(kls, guid):
        return kls._registry[guid]

class Sink(Protocol):
    def source_changed(source) -> None:
        pass
