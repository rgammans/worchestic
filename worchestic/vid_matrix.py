# vid_matrix.py - Video matrix controll logic

from contextlib import suppress
from dataclasses import dataclass
from typing import Union, ForwardRef
from .signals import Source
from atomicx import AtomicInt
import logging

logger = logging.getLogger(__name__)

class LockedOutput(ValueError):
    pass


class AlreadyUnlocked(ValueError):
    pass


class UnroutableOutput(ValueError):
    pass

class MatrixOutput:
    """A Matrix output is a source, which is
    the output of a specrific discoverable matrix"""
    def __init__(self, device: ForwardRef('Matrix'), idx: int):
        self._source = None
        self._sem = AtomicInt(0)
        self._device = device
        self._idx = idx

    def __str__(self):
        return f"{self._device.name}.outputs[{self._idx}]"

    @property
    def port(self):
        return self._device, self._idx

    @property
    def locked(self):
        return bool(self._sem.load())

    @property
    def uuid(self):
        """Unique Identifier for the current signal on this output/cable"""
        return self._source and self._source.uuid

    def select(self, src: ForwardRef('InputSignal'), nolock: bool = False):
        """Select an alternate signal for this ouptut, locking the output"""
        if src.uuid != self.uuid:
            if self.locked:
                raise LockedOutput(f"{self} is locked/in use")
            self._device.select(self._idx, src)
            self._source = src
        if not nolock:
            self.claim()

    def release(self):
        """Release a lock on the output"""
        self._sem.dec()
        if self._sem.load() < 0:
            # Attempt to recover!
            self._sem.inc()
            raise AlreadyUnlocked("Invalid lock state")
        self._device.release(self._idx)

    def claim(self):
        """Claim a lock on the output"""
        self._sem.inc()


class MatrixDriver:
    def select(input: int, output: int):
        raise NotImplementedError()


InputSignal = Union[MatrixOutput, Source]


class Matrix:
    """An instance of this class
    represents a single switch element"""
    def __init__(self, name: str, driver: MatrixDriver, inputs: InputSignal,
                 nr_outputs: int):
        self.name = name
        self._driver = driver
        self.inputs = inputs
        self.outputs = [None] * nr_outputs
        self._current = {}
        for idx in range(nr_outputs):
            self.outputs[idx] = MatrixOutput(self, idx)

    def __str__(self):
        return self.name

    @dataclass
    class AvailableSource:
        input_idx: int
        path_len: int
        path: InputSignal
        source: Source

    @property
    def available_sources(self):
        """List the available sources for this matrix"""
        return set(x.source for x in self.iter_sources())

    def iter_sources(self):
        for idx, inp in enumerate(self.inputs):
            if isinstance(inp, MatrixOutput):
                if inp.locked:
                    # If the input is locked don't recurse.
                    # but it is availibl itself.
                    logger.debug(f"locked - {idx}, {inp}")
                    yield self.AvailableSource(idx,  0, inp, inp._source)
                    continue

                for source in inp.port[0].iter_sources():
                    logger.debug(f"unlocked - {idx}, {source.source.uuid}")
                    yield self.AvailableSource(idx, source.path_len + 1,
                                               inp, source.source)
            else:
                yield self.AvailableSource(idx, 1, inp, inp)

    def select(self, idx, source: Source):
        """Sets output (idx) to connect to source

        Propagates up the switch fabric as necessary.
        """
        logger.info(f"{self}: assigning {idx} to {source.uuid}")
        self.release(idx)

        routes = [s for s in self.iter_sources() if s.source == source]
        if not routes:
            raise UnroutableOutput(f"{self}:{source.uuid} is not routable to output {idx}")

        route = min(routes, key=lambda s: s.path_len)
        if isinstance(route.path, MatrixOutput):
            logger.info(f"({self})Using output {route.path}({route.path_len}) "
                        f"for {idx}")
            route.path.select(route.source)
        self._driver.select(idx, route.input_idx)
        self._current[idx] = route.input_idx

    def release(self, idx):
        """Releases a hold on any signal apatch which feed this input

           - Allows the currently used input for this output to be switched
             to a differnet signal
        """
        try:
            current = self.inputs[self._current[idx]]
            current.release()
            logger.debug(f"released {current and current.uuid}")
        except (KeyError, AttributeError) as e:
            logger.debug(f"skipping release: {e!r}")
