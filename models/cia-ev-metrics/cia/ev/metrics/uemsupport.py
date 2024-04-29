
from pyannote.metrics.utils import UEMSupportMixin
import warnings
from pyannote.core import Timeline, Segment

class MausicUEMSupportMixin (UEMSupportMixin):

    def extend_uemify(self, reference, hypothesis, uem=None, tolerance=0.,
               skip_overlap=False, returns_uem=False, returns_timeline=False):

        """Crop 'reference' and 'hypothesis' to 'uem' support
        Parameters
        ----------
        reference, hypothesis : Annotation
            Reference and hypothesis annotations.
        uem : Timeline, optional
            Evaluation map.
        tolerance : float, optional
            When provided, set the duration of tolerance centered around
            reference segment boundaries that are extended from both reference
            and hypothesis. Defaults to 0. (i.e. no collar).
        skip_overlap : bool, optional
            Set to True to not evaluate overlap regions.
            Defaults to False (i.e. keep overlap regions).
        returns_uem : bool, optional
            Set to True to return extruded uem as well.
            Defaults to False (i.e. only return reference and hypothesis)
        returns_timeline : bool, optional
            Set to True to oversegment reference and hypothesis so that they
            share the same internal timeline.
        Returns
        -------
        reference, hypothesis : Annotation
            Extended reference and hypothesis annotations
        uem : Timeline
            Extruded uem (returned only when 'returns_uem' is True)
        timeline : Timeline:
            Common timeline (returned only when 'returns_timeline' is True)
        """

        # when uem is not provided, use the union of reference and hypothesis
        # extents -- and warn the user about that.
        if uem is None:
            r_extent = reference.get_timeline().extent()
            h_extent = hypothesis.get_timeline().extent()
            extent = r_extent | h_extent
            uem = Timeline(segments=[extent] if extent else [],
                           uri=reference.uri)
            warnings.warn(
                "'uem' was approximated by the union of 'reference' "
                "and 'hypothesis' extents.")

        # extrude collars (and overlap regions) from uem
        uem = self.extrude(uem, reference, collar=collar,
                           skip_overlap=skip_overlap)

        # extrude regions outside of uem
        reference = reference.crop(uem, mode='intersection')
        hypothesis = hypothesis.crop(uem, mode='intersection')

        # project reference and hypothesis on common timeline
        if returns_timeline:
            timeline = self.common_timeline(reference, hypothesis)
            reference = self.project(reference, timeline)
            hypothesis = self.project(hypothesis, timeline)

        result = (reference, hypothesis)
        if returns_uem:
            result += (uem, )

        if returns_timeline:
            result += (timeline, )

        return result