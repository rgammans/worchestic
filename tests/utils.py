""" Util functions used in multiple unittests"""
from worchestic.signals import Source


def make_signal(name=""):
    """Creates a signal useful for log messages during testing
    Speficically it set the name to the str of the uuid
    """
    s = Source(name)
    if not name:
        s.name = str(s.uuid)
    return s
