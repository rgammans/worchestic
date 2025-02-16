from contextlib import suppress

class SourceGroup:
    """Manages groups of signal sources with companion relationships and output assignments.

    This class handles the organization of signal sources into groups and manages their
    relationships and preferred outputs. It allows for automatic assignment of outputs
    to signals and provides functionality to find companion signals across groups.

    Signals are placed into groups, and the position of a signal in one group is used
    to determine its companions in other groups. Companion signals are signals that
    share the same position in other groups.

    Args:
        **kwargs: Keyword arguments where:
            - Keys are group names
            - Values are lists/sequences of signal sources
            - Special key 'assign_outputs' can contain a dict mapping group names to
              preferred outputs for all signals in that group

    Examples:
        >>> sources = SourceGroup(
        ...     video=['hdmi1', 'hdmi2'],
        ...     audio=['optical1', 'optical2'],
        ...     assign_outputs={'video': vid_matrix.outputs[0], 'audio': audio_amp.outputs[0]}
        ... )
        >>> sources.get_companions('hdmi1')
        {'optical1'}

    Attributes:
        groups (dict): Dictionary containing the group names and their associated signal source
    """
    def __init__(self, /, **kwargs):
        self.groups = kwargs
        if assignments := kwargs.pop('assign_outputs', None):
            for grp, output in assignments.items():
                for signal in self.groups[grp]:
                    signal.preferred_out = output

    def get_companions(self, source):
        """Get all sources at same index position across groups.

        For a given source, finds all other sources that appear at the same index position
        in different groups. The source must exist in at least one group to find companions.

        Args:
            source: The source object to find companions for

        Returns:
            set: A set of companion sources found at the same index position across groups.
                 Returns empty set if source is not found in any group.

        Example:
            If groups contain:
            group1 = [A, B, C]
            group2 = [D, E, F]

            get_companions(B) would return {E} since B and E are both at index 1
        """
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
                    if companion is not None and companion is not source:
                        rv.add(companion)
            return rv

        return set()


class MatrixGroup:
    """Manages groups of matrices and their signal routing.

    This class coordinates multiple matrices and their signal sources, handling automatic
    companion signal routing across different matrices when a source is selected.

        signalgrp (SourceGroup): The signal group containing source relationships
            - Keys are matrix names
            - Values are matrix objects that handle the actual signal routing

        >>> matrix_group = MatrixGroup(
        ...     signal_sources,
        ...     video=video_matrix,
        ...     audio=audio_matrix
        >>> matrix_group.select('video', 0, 'hdmi1')  # Routes hdmi1 and its audio companion

        signals (SourceGroup): The signal group managing source relationships
        matrices (dict): Dictionary containing the matrices by name
    """
    def __init__(self, signalgrp, **kwargs):
        self.signals = signalgrp
        self.matrices = kwargs

    def select(self, matrix, idx, src, no_companions=False):
        """
        Select a source for a specific output in a matrix and handle companion signals.

        Args:
            matrix (str): The identifier of the matrix to operate on
            idx (int): The output index in the matrix to select to
            src (Signal): The source signal to select
            no_companions (bool, optional): If True, skip handling companion signals. Defaults to False.

        This method performs the following:
        1. Gets the specified matrix and selects the source to the given output index
        2. If companions are enabled, finds companion signals and routes them to their preferred outputs
        """
        mat = self.matrices[matrix]
        mat.select(idx, src)
        mat_out = mat.outputs[idx]

        if not no_companions:
            companions = self.signals.get_companions(src)
            for other_src in companions:
                # Skip if no grouped signal for this poisition
                outp = other_src.preferred_out
                if outp and outp is not mat_out:
                    outp.select(other_src, nolock=True)
                else:
                    print(f"skipping {other_src}, no pref output")

    def get_output(self, name, idx: int):
        return self.matrices[name].outputs[idx]

    def available(self, group):
        return self.matrices[group].available_sources
