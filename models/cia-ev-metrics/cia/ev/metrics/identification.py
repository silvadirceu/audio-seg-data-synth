from pyannote.core import Annotation, Segment, Timeline

from pyannote.metrics.matcher import (
    MATCH_CORRECT,
    MATCH_CONFUSION,
    MATCH_MISSED_DETECTION,
    MATCH_FALSE_ALARM,
    MATCH_TOTAL,
)

from pyannote.metrics.errors.identification import IdentificationErrorAnalysis

from .musicannotation import extend


REFERENCE_TOTAL = "reference"
HYPOTHESIS_TOTAL = "hypothesis"

REGRESSION = "regression"
IMPROVEMENT = "improvement"
BOTH_CORRECT = "both_correct"
BOTH_INCORRECT = "both_incorrect"

MATCH_CORRECT_TP = "correct tp"  # all matches in a reference segment
MATCH_CORRECT_DAP = "correct dap"  # one match per reference segment
MATCH_TOTAL_HYP = "total hyp"


class IdentificationErrorAnalysisMusic(IdentificationErrorAnalysis):
    """
    Parameters
    ----------
    collar : float, optional
        Duration (in seconds) of collars removed from evaluation around
        boundaries of reference segments.
    skip_overlap : bool, optional
        Set to True to not evaluate overlap regions.
        Defaults to False (i.e. keep overlap regions).
    """

    def __init__(self, collar=0.0, skip_overlap=False):
        super(IdentificationErrorAnalysisMusic, self).__init__(
            collar=collar, skip_overlap=skip_overlap
        )

        self.results = {}

    def music_difference(self, reference, hypothesis, tolerance=0.0, bounds=(-1, -1)):
        """Get error analysis as `Annotation`
        Labels are (status, reference_label, hypothesis_label) tuples.
        `status` is either 'correct', 'confusion', 'missed detection' or
        'false alarm'.
        `reference_label` is None in case of 'false alarm'.
        `hypothesis_label` is None in case of 'missed detection'.
        Parameters
        ----------
        uemified : bool, optional
            Returns "uemified" version of reference and hypothesis.
            Defaults to False.
        Returns
        -------
        errors : `Annotation`
        """

        counts = {
            MATCH_MISSED_DETECTION: 0,
            MATCH_FALSE_ALARM: 0,
            MATCH_CORRECT_TP: 0,
            MATCH_CORRECT_DAP: 0,
            MATCH_TOTAL: 0,
            MATCH_TOTAL_HYP: 0,
            MATCH_CONFUSION: 0,
        }

        errors = Annotation(
            uri=(reference.uri, hypothesis.uri), modality=reference.modality
        )

        # Compute MATCH_CORRECT_TP, MATCH_CORRECT_DAP and MATCH_MISSED_DETECTION

        for seg_ref in reference.get_timeline():
            ref_label = reference.get_labels(seg_ref, unique=False)[0]
            h_timeline = hypothesis.label_support(ref_label)

            if h_timeline:
                match_i = []
                is_found = False
                is_miss_detection = True
                for seg_hyp in h_timeline:
                    if seg_hyp.intersects(
                        extend(seg_ref, tolerance=tolerance, bounds=bounds)
                    ):
                        match_i.append(ref_label[0])

                        is_miss_detection &= False

                        track = errors.new_track(seg_hyp, prefix=MATCH_CORRECT_TP)
                        errors[seg_hyp, track] = (
                            MATCH_CORRECT_TP,
                            ref_label,
                            ref_label,
                        )

                        if not is_found:
                            track = errors.new_track(seg_hyp, prefix=MATCH_CORRECT_DAP)
                            errors[seg_hyp, track] = (
                                MATCH_CORRECT_DAP,
                                ref_label,
                                ref_label,
                            )
                            is_found = True

                if is_miss_detection:
                    counts[MATCH_MISSED_DETECTION] += 1

                    track = errors.new_track(seg_ref, prefix=MATCH_MISSED_DETECTION)
                    errors[seg_ref, track] = (MATCH_MISSED_DETECTION, ref_label, "-")

                if len(match_i) > 0:
                    counts[MATCH_CORRECT_TP] += len(match_i)
                    counts[MATCH_CORRECT_DAP] += len(set(match_i))

            else:
                counts[MATCH_MISSED_DETECTION] += 1

                track = errors.new_track(seg_ref, prefix=MATCH_MISSED_DETECTION)
                errors[seg_ref, track] = (MATCH_MISSED_DETECTION, ref_label, "-")

        # Compute MATCH_FALSE_ALARM
        for idx, seg_hyp in enumerate(hypothesis.get_timeline()):
            hyp_label = hypothesis.get_labels(seg_hyp, unique=False)[0]
            r_timeline = reference.label_support(hyp_label)

            if r_timeline:
                for seg_ref in r_timeline:
                    I = False
                    if seg_hyp.intersects(
                        extend(seg_ref, tolerance=tolerance, bounds=bounds)
                    ):
                        I = True
                        break

                if not I:
                    counts[MATCH_FALSE_ALARM] += 1

                    for s_ref in reference.get_timeline():
                        if seg_hyp.intersects(s_ref):
                            counts[MATCH_CONFUSION] += 1

                    track = errors.new_track(seg_hyp, prefix=MATCH_FALSE_ALARM)
                    errors[seg_hyp, track] = (MATCH_FALSE_ALARM, "-", hyp_label)
            else:
                counts[MATCH_FALSE_ALARM] += 1
                track = errors.new_track(seg_hyp, prefix=MATCH_FALSE_ALARM)
                errors[seg_hyp, track] = (MATCH_FALSE_ALARM, "-", hyp_label)

                for s_ref in reference.get_timeline():
                    if seg_hyp.intersects(s_ref):
                        counts[MATCH_CONFUSION] += 1

        counts[MATCH_TOTAL] = len(reference)
        counts[MATCH_TOTAL_HYP] = len(hypothesis)

        DAP = counts[MATCH_CORRECT_DAP] / len(reference)
        self.results = {"counts": counts, "dap": DAP, "errors": errors.for_json()}

        return self.results

    def for_json(self):
        new_results = self.results.copy()
        new_results["errors"] = self.results["errors"].for_json()

        return new_results


class IdentificationErrorAnalysisMusicECAD(IdentificationErrorAnalysis):
    """
    Parameters
    ----------
    collar : float, optional
        Duration (in seconds) of collars removed from evaluation around
        boundaries of reference segments.
    skip_overlap : bool, optional
        Set to True to not evaluate overlap regions.
        Defaults to False (i.e. keep overlap regions).
    """

    def __init__(self, collar=0.0, skip_overlap=False):
        super(IdentificationErrorAnalysisMusicECAD, self).__init__(
            collar=collar, skip_overlap=skip_overlap
        )

        self.results = {}

    def music_difference(self, reference, hypothesis, tolerance=0.0, bounds=(-1, -1)):
        """Get error analysis as `Annotation`
        Labels are (status, reference_label, hypothesis_label) tuples.
        `status` is either 'correct', 'confusion', 'missed detection' or
        'false alarm'.
        `reference_label` is None in case of 'false alarm'.
        `hypothesis_label` is None in case of 'missed detection'.
        Parameters
        ----------
        uemified : bool, optional
            Returns "uemified" version of reference and hypothesis.
            Defaults to False.
        Returns
        -------
        errors : `Annotation`
        """

        counts = {
            MATCH_MISSED_DETECTION: 0,
            MATCH_FALSE_ALARM: 0,
            MATCH_CORRECT_TP: 0,
            MATCH_CORRECT_DAP: 0,
            MATCH_TOTAL: 0,
            MATCH_TOTAL_HYP: 0,
            MATCH_CONFUSION: 0,
        }

        errors = Annotation(
            uri=(reference.uri, hypothesis.uri), modality=reference.modality
        )

        # Compute MATCH_CORRECT_TP, MATCH_CORRECT_DAP and MATCH_MISSED_DETECTION

        for seg_ref in reference.get_timeline():
            ref_label = reference.get_labels(seg_ref, unique=False)[0]
            h_timeline = hypothesis.label_support(ref_label)

            if h_timeline:
                match_i = []
                is_found = False
                is_miss_detection = True
                for seg_hyp in h_timeline:
                    if seg_hyp.intersects(
                        extend(seg_ref, tolerance=tolerance, bounds=bounds)
                    ):
                        match_i.append(ref_label[0])

                        is_miss_detection &= False

                        track = errors.new_track(seg_hyp, prefix=MATCH_CORRECT_TP)
                        errors[seg_hyp, track] = (
                            MATCH_CORRECT_TP,
                            ref_label,
                            ref_label,
                        )

                        if not is_found:
                            track = errors.new_track(seg_hyp, prefix=MATCH_CORRECT_DAP)
                            errors[seg_hyp, track] = (
                                MATCH_CORRECT_DAP,
                                ref_label,
                                ref_label,
                            )
                            is_found = True

                if is_miss_detection:
                    counts[MATCH_MISSED_DETECTION] += 1

                    track = errors.new_track(seg_ref, prefix=MATCH_MISSED_DETECTION)
                    errors[seg_ref, track] = (MATCH_MISSED_DETECTION, ref_label, "-")

                if len(match_i) > 0:
                    counts[MATCH_CORRECT_TP] += len(match_i)
                    counts[MATCH_CORRECT_DAP] += len(set(match_i))

            else:
                counts[MATCH_MISSED_DETECTION] += 1

                track = errors.new_track(seg_ref, prefix=MATCH_MISSED_DETECTION)
                errors[seg_ref, track] = (MATCH_MISSED_DETECTION, ref_label, "-")

        # Compute MATCH_FALSE_ALARM
        for idx, seg_hyp in enumerate(hypothesis.get_timeline()):
            hyp_label = hypothesis.get_labels(seg_hyp, unique=False)[0]
            r_timeline = reference.label_support(hyp_label)

            if r_timeline:
                for seg_ref in r_timeline:
                    I = False
                    if seg_hyp.intersects(
                        extend(seg_ref, tolerance=tolerance, bounds=bounds)
                    ):
                        I = True
                        break

                if not I:
                    counts[MATCH_FALSE_ALARM] += 1

                    for s_ref in reference.get_timeline():
                        if seg_hyp.intersects(s_ref):
                            counts[MATCH_CONFUSION] += 1

                            track = errors.new_track(seg_hyp, prefix=MATCH_CONFUSION)
                            errors[seg_hyp, track] = (MATCH_CONFUSION, "-", hyp_label)

                    track = errors.new_track(seg_hyp, prefix=MATCH_FALSE_ALARM)
                    errors[seg_hyp, track] = (MATCH_FALSE_ALARM, "-", hyp_label)
            else:
                counts[MATCH_FALSE_ALARM] += 1
                track = errors.new_track(seg_hyp, prefix=MATCH_FALSE_ALARM)
                errors[seg_hyp, track] = (MATCH_FALSE_ALARM, "-", hyp_label)

                for s_ref in reference.get_timeline():
                    if seg_hyp.intersects(s_ref):
                        counts[MATCH_CONFUSION] += 1

                        track = errors.new_track(seg_hyp, prefix=MATCH_CONFUSION)
                        errors[seg_hyp, track] = (MATCH_CONFUSION, "-", hyp_label)

        counts[MATCH_TOTAL] = len(reference)
        counts[MATCH_TOTAL_HYP] = len(hypothesis)

        DAP = counts[MATCH_CORRECT_DAP] / len(reference)

        self.results = {"counts": counts, "dap": DAP, "errors": errors.for_json()}

        return self.results

    def for_json(self):
        new_results = self.results.copy()
        new_results["errors"] = self.results["errors"].for_json()

        return new_results
