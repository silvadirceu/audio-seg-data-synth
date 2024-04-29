from pyannote.core import Annotation, Segment, Timeline
from typing import Optional


def extend(segment, tolerance=0.0, bounds=(-1, -1)) -> Segment:
    """Extent

    The extent of a timeline is the segment of minimum duration that
    contains every segments of the timeline. It is unique, by definition.
    The extent of an empty timeline is an empty segment.

    A picture is worth a thousand words::

                timeline
                |------|

        timeline.extended()
         |----------------------|
    tolerance -|------|- tolerance

    Returns
    -------
    extent : Segment
        Timeline extended

    Examples
    --------
    >>> timeline = extend(Timeline(segments=[Segment(0, 1)], tolerance = 3.0)
    <Segment(0, 4.0)>

    """

    if tolerance > 0.0:
        segments_start, segment_end = segment.start, segment.end
        start = segments_start - tolerance
        end = segment_end + tolerance

        if bounds[0] != -1:
            start = max(segments_start - tolerance, bounds[0])
        if bounds[1] != -1:
            end = min(segment_end + tolerance, bounds[1])

        return Segment(start=start, end=end)

    return segment


class MusicAnnotation(Annotation):

    def __init__(self, uri: Optional[str] = None, modality: Optional[str] = None):

        super(MusicAnnotation, self).__init__(uri, modality)

    def support(segs: Annotation, collar: float = 0.0) -> "Annotation":
        """Annotation support

        The support of an annotation is an annotation where contiguous tracks
        with same label are merged into one unique covering track.

        A picture is worth a thousand words::

            collar
            |---|

            annotation
            |--A--| |--A--|     |-B-|
              |-B-|    |--C--|     |----B-----|

            annotation.support(collar)
            |------A------|     |------B------|
              |-B-|    |--C--|

        Parameters
        ----------
        collar : float, optional
            Merge tracks with same label and separated by less than `collar`
            seconds. This is why 'A' tracks are merged in above figure.
            Defaults to 0.

        Returns
        -------
        support : Annotation
            Annotation support without new tracks

        Note
        ----
        Track names are lost in the process.
        """
        # initialize an empty annotation
        # with same uri and modality as original
        support = segs.empty()

        for label in segs.labels():

            # get timeline for current label
            timeline = segs.label_timeline(label, copy=True)

            # fill the gaps shorter than collar
            timeline = timeline.support(collar)
            # timeline = Timeline(segments = support_iter(timeline, collar))
            # reconstruct annotation with merged tracks
            for segment in timeline.support():
                support[segment] = label

        return support

    def seq_support(self, collar: float = 0.0):
        """Annotation sequencial support

        The support of an annotation is an annotation where contiguous tracks
        with same label without any other label between are merged into one unique covering track.

        A picture is worth a thousand words::

            collar
            |---|

            annotation
            |--A--| |-B-| |--A--|    |-B-|
                                        |----B-----|

            annotation.seq_support(collar)
            |--A--| |-B-| |--A--|    |------B------|

            annotation
            |--A--|  |--A--|    |-B-|
                                  |----B-----|

            annotation.seq_support(collar)
            |-------A------|    |------B------|


        Parameters
        ----------
        collar : float, optional
            Merge tracks with same label and separated by less than `collar`
            seconds. This is why 'A' tracks are merged in above figure.
            Defaults to 0.

        Returns
        -------
        support : Annotation
            Annotation support

        Note
        ----
        Track names are lost in the process.
        """

        # initialize an empty annotation
        # with same uri and modality as original
        support = MusicAnnotation()

        old_label = ""
        segs_annotation = list(self.itertracks(yield_label=True))
        new_label = segs_annotation[0][2]
        new_segment = segs_annotation[0][0]

        for segment, track, label in segs_annotation:

            # If there is no gap between new support segment and next segment
            # OR there is a gap with duration < collar seconds,

            possible_gap = segment ^ new_segment
            if (label == new_label) and (
                not possible_gap or possible_gap.duration < collar
            ):
                # Extend new support segment using next segment
                new_segment |= segment

            # If there actually is a gap and the gap duration >= collar
            # seconds,
            else:
                support[new_segment] = new_label

                # Initialize new support segment as next segment
                # (right after the gap)
                new_segment = segment
                new_label = label

        if not new_segment in support:
            support[new_segment] = new_label

        return support

    @classmethod
    def from_txt(cls, filename: str, start=None, end=None, map_labels=None):
        annotation = MusicAnnotation()
        with open(filename, "r") as file:
            for line in file:
                star_f, end_f, label_f = line.strip().split()
                star_f, end_f = float(star_f), float(end_f)

                if start is not None and end is not None:
                    if end_f <= start or star_f >= end:
                        continue
                    star_f = max(star_f, start)
                    end_f = min(end_f, end)

                if map_labels:
                    label_f = map_labels(label_f)

                segment = Segment(star_f, end_f)

                annotation[segment] = label_f

        return annotation

    def segmentation(self):
        timeline: list[Segment] = self.get_timeline()
        segments_to_remove = set()
        for seg1 in timeline:
            for seg2 in timeline:
                if seg1 == seg2:
                    continue
                if seg1.start >= seg2.start and seg1.end <= seg2.end:
                    segments_to_remove.add(seg1)
                    break
                elif seg2.start >= seg1.start and seg2.end <= seg1.end:
                    segments_to_remove.add(seg2)
                    break

        new_annotation = MusicAnnotation()
        for seg in timeline:
            if seg not in segments_to_remove:
                new_annotation[seg] = self[seg]

        return new_annotation

    def save(self, filename: str):
        with open(filename, 'w') as file:
            timeline: list[Segment] = self.get_timeline()
            for seg in timeline:
                file.write(f"{seg.start:.5f}\t{seg.end:.5f}\t{self[seg]}\n")

    