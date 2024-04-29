
import numpy as np
from pyannote.core import Segment, Timeline, Annotation

from pyannote.metrics.base import BaseMetric, f_measure

from pyannote.metrics.segmentation import (PURITY_NAME, COVERAGE_NAME, PURITY_COVERAGE_NAME, PTY_CVG_TOTAL,
                                            PTY_CVG_INTER, PTY_TOTAL, PTY_INTER, CVG_TOTAL, CVG_INTER)


DETAIL_INTER = 'intersection detail'

class SegmentationPurityCoverageFMeasureMusic(BaseMetric):
    """Segmentation coverage
    Parameters
    ----------
    tolerance : float, optional
        When provided, preprocess reference by filling intra-label gaps shorter
        than `tolerance` (in seconds).
    """

    def __init__(self, tolerance=0.500, beta=1, **kwargs):
        super(SegmentationPurityCoverageFMeasureMusic, self).__init__(**kwargs)
        self.tolerance = tolerance
        self.beta = beta
        self.datail_intersect = None

    def _process(self, reference, hypothesis, uem=None):

        detail = self.init_components()

        errors = Annotation(uri=reference.uri, modality=reference.modality)

        intersection = 0.
        total_cvg = 0.
        total_pty = 0.

        # loop on all segments
        for segment in reference.get_timeline():
            ref_label = reference.get_labels(segment, unique=False)[0]
            h_timeline = hypothesis.label_support(ref_label)

            total_cvg += segment.duration

            for h in h_timeline:
                seg_intersec = segment & h

                if segment.intersects(h):
                    track = errors.new_track(segment, prefix=CVG_INTER)
                    errors[segment, track] = (CVG_INTER, ref_label, "{:.2f} seg".format(seg_intersec.duration))

                    intersection += seg_intersec.duration

        for h in hypothesis.get_timeline():
            total_pty += h.duration

        detail[CVG_TOTAL] = total_cvg
        detail[CVG_INTER] = intersection

        detail[PTY_TOTAL] = total_pty
        detail[PTY_INTER] = intersection

        self.datail_intersect = errors

        return detail

    def compute_components(self, reference, hypothesis, **kwargs):
        return self._process(reference, hypothesis)

    def compute_metric(self, detail):
        _, _, value = self.compute_metrics(detail=detail)
        return value

    def compute_metrics(self, detail=None):
        detail = self.accumulated_ if detail is None else detail

        purity = \
            1. if detail[PTY_TOTAL] == 0. \
            else detail[PTY_INTER] / detail[PTY_TOTAL]

        coverage = \
            1. if detail[CVG_TOTAL] == 0. \
            else detail[CVG_INTER] / detail[CVG_TOTAL]

        return purity, coverage, f_measure(purity, coverage, beta=self.beta)

    @classmethod
    def metric_name(cls):
        return PURITY_COVERAGE_NAME

    @classmethod
    def metric_components(cls):
        return [CVG_TOTAL, CVG_INTER, PTY_TOTAL, PTY_INTER]

    def get_intersect_detail(self):
        return self.datail_intersect.for_json()