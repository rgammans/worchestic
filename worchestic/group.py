from contextlib import suppress


class SourceGroup:
    def __init__(self, /, **kwargs):
        self.groups = kwargs

    def get_companions(self, source):
        idx = None
        for sourceset in self.groups.values():
            with suppress(ValueError):
                idx = sourceset.index(source)
                break

        if idx is not None:
            rv = set()
            for sourceset in self.groups.values():
                with suppress(IndexError):
                    companion = sourceset[idx]
                    if companion is not source:
                        rv.add(companion)
            return rv

        return set()


class MatrixGroup:
    def __init__(self, signalgrp, **kwargs):
        self.signals = signalgrp
        self.matricies = kwargs

    def select(self, matrix, idx, src, no_companions=False):
        mat = self.matricies[matrix]
        mat.select(idx, src)
        mat_out = mat.outputs[idx]

        if not no_companions:
            companions = self.signals.get_companions(src)
            for other_src in companions:
                outp = other_src.preferred_out
                if outp and outp is not mat_out:
                    outp.select(other_src, nolock=True)
