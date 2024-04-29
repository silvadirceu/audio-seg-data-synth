from pyannote.core import Annotation, Segment, Timeline

from .identification import IdentificationErrorAnalysisMusicECAD
from .musicannotation import MusicAnnotation
from .segmentation import SegmentationPurityCoverageFMeasureMusic


def create_context(
    segments: MusicAnnotation, validLabels=None, endfile=None, onlysongs=True
):
    start = 0.0
    s = list(segments.itertracks(yield_label=True))[-1]
    end = s[0].end
    validSegs = None
    new_ref = None

    if endfile is not None:
        end = endfile

    if validLabels is not None:
        valid = validLabels.copy()

        refLabels = segments.labels()  # get all labels
        if not onlysongs:
            valid.append("0")

        dif_labels = list(set(refLabels) - set(valid))  # compute set difference
        dif_segs = segments.subset(
            labels=dif_labels
        )  # get segments and labels with labels of diff
        segsList_to_del = [
            seg[0] for seg in dif_segs.itertracks(yield_label=True)
        ]  # get segments only
        segs_to_del = Timeline(segments=segsList_to_del)  # create a new timeline
        new_ref = segments.extrude(
            removed=segs_to_del, mode="intersection"
        )  # delete segments not valid
        if len(new_ref) > 0:
            validSegs = new_ref.get_timeline()  # get new timeline -- valid timeline
            validSegs = validSegs.support()
        else:
            new_ref = None

    else:
        validSegs = [Segment(start, end)]
        new_ref = segments

    return new_ref  # , Timeline(segments=validSegs)


def parse_Dic2Segs(listdic, name=None, onlysongs=True, filesize=None):
    """
    Convert Audacity to Annotation type
    parameters
    listdic: list of dictionaries [{"obra":, "inicio":, "fim":}]
            vector of segments begin time
    name: str
            name of the file or task
    onlysongs: bool
            consider only songs segments or all time of the file inserting zeros between songs
    filesize: float
            time in seconds of the file, used when onlusongs = True

    return:
    segs: Annotation Type
            List of the Segments
    """

    segs = MusicAnnotation(uri=name)

    for d in listdic:
        segs[Segment(d["inicio"], d["fim"])] = d["obra"]

    segs = segs.rename_labels({0: "0"})

    if not onlysongs:
        s = list(segs.itertracks(yield_label=True))[-1]
        end = s[0].end

        if filesize is not None:
            end = filesize

        all_timeline = Timeline(segments=[Segment(0.0, end)])
        all_marks = [seg[0] for seg in segs.itertracks(yield_label=True)]
        new_segs = all_timeline.extrude(
            removed=Timeline(segments=all_marks), mode="intersection"
        )
        for nseg in new_segs:
            segs[nseg] = "0"

    return segs


def parse_Lists2Segs(
    beginlist, endlist, labels, name=None, onlysongs=True, filesize=None
):
    """
    Convert Audacity to Annotation type
    parameters
    beginlit: list
            vector of segments begin time
    endlist: list
            vector segments end time
    labels: list
            vector labels of segments
    name: str
            name of the file
    onlysongs: bool
            consider only songs segments or all time of the file inserting zeros between songs
    filesize: float
            time in seconds of the file, used when onlusongs = True

    return:
    segs: Annotation Type
            List of the Segments
    """

    segs = MusicAnnotation(uri=name)

    for b, e, label in zip(beginlist, endlist, labels):
        segs[Segment(b, e)] = label

    if not onlysongs:
        s = list(segs.itertracks(yield_label=True))[-1]
        end = s[0].end

        if filesize is not None:
            end = filesize

        all_timeline = Timeline(segments=[Segment(0.0, end)])
        all_marks = [seg[0] for seg in segs.itertracks(yield_label=True)]
        new_segs = all_timeline.extrude(
            removed=Timeline(segments=all_marks), mode="intersection"
        )
        for nseg in new_segs:
            segs[nseg] = "0"

    return segs


def preprocess_results(manualMarks, autoMarks, name=None, endfile=None):
    """
    manualMarks: list of dict [{"obra":, "inicio":, "fim":}]
            list of dictionaries with keys obra, inicio and fim from manual auditory

    autoMarks: list of dict [{"obra":, "inicio":, "fim":}]
            list of dictionaries with keys obra, inicio and fim from automatic system

    name: string
            task name or code

    withcontext: bool
            used join to validaLabels to specify the labels to consider in the metrics

    validLabels: list
            list with te labels to consider in the metrics

    return:
    segs_ref, segs_auto: Annotation Type
            List of the Segments for refrences and predicted
    """

    # Reference
    segs_ref = parse_Dic2Segs(manualMarks, name=name)

    # Automatic
    segs_auto = parse_Dic2Segs(autoMarks, name=name)

    if endfile is not None:
        endtime = endfile
    else:
        endtime = manualMarks[-1]["fim"]

    dict_marks = {"name": name, "ref": segs_ref, "end": endtime, "auto": segs_auto}

    return dict_marks


def compute_segmentation_metrics(
    marks_dictionary=None, ref=None, hyp=None, tolerance=0.5, context=None
):
    cvg_pty = SegmentationPurityCoverageFMeasureMusic(tolerance=tolerance)

    if marks_dictionary is not None:
        ref = marks_dictionary["ref"]
        hyp = marks_dictionary["auto"]

    result = cvg_pty(ref, hyp, detailed=True, uem=context)

    coverage = result["cvg intersection duration"] / result["cvg total duration"]
    purity = result["pty intersection duration"] / result["pty total duration"]
    F = result["segmentation F[purity|coverage]"]
    detail = cvg_pty.get_intersect_detail()

    return coverage, purity, F, detail


def compute_identification_metrics(
    marks_dictionary=None,
    ref=None,
    hyp=None,
    collar=1.0,
    tolerance=0.0,
    bounds=(-1, -1),
):
    idt_error = IdentificationErrorAnalysisMusicECAD(collar=collar)

    if marks_dictionary is not None:
        ref = marks_dictionary["ref"]
        hyp = marks_dictionary["auto"]

    error_analysis = idt_error.music_difference(
        ref, hyp, tolerance=tolerance, bounds=bounds
    )

    return error_analysis


def compute_metrics(
    marks_dict=None,
    Ref=None,
    Hyp=None,
    withcontext=True,
    tolerance=0.0,
    validLabels=None,
    endfile=None,
):
    coverage = 0.0
    purity = 0.0
    F = 0.0
    detail = 0.0
    error_analysis = {}

    if marks_dict is not None:
        marksRef = marks_dict["ref"]
        s = list(marksRef.itertracks())[-1]
        endTime = s[0].end
    else:
        marksRef = Ref
        s = list(marksRef.itertracks())[-1]
        endTime = s[0].end

    if endfile is not None:
        endTime = endfile

    ref_original = Ref.copy()
    if withcontext:
        Ref = create_context(
            Ref, validLabels=validLabels, endfile=endTime, onlysongs=True
        )

    if Ref is not None:
        error_analysis = compute_identification_metrics(
            marks_dictionary=marks_dict,
            ref=Ref,
            hyp=Hyp,
            collar=1.0,
            tolerance=tolerance,
            bounds=(0.0, -1),
        )

        coverage, purity, F, detail = compute_segmentation_metrics(
            marks_dictionary=marks_dict, ref=Ref, hyp=Hyp, tolerance=0.5
        )

        error_analysis["counts"]["total musics audit"] = len(ref_original)
        error_analysis["dlp"] = coverage
        error_analysis["purity"] = purity
        error_analysis["F"] = F
        error_analysis["detail_segmentation"] = detail

    return error_analysis


def compute_metrics_api(
    reference_json,
    name_ref,
    hypothesis_json,
    name_hyp,
    withcontext=False,
    validLabels=None,
    endfile=None,
    tolerance=0.0,
):
    Ref = parse_Dic2Segs(
        reference_json, name=name_ref, filesize=endfile, onlysongs=True
    )
    Ref = Ref.seq_support()

    Hyp = parse_Dic2Segs(
        hypothesis_json, name=name_hyp, filesize=endfile, onlysongs=True
    )
    Hyp = Hyp.seq_support()

    error_analysis = compute_metrics(
        Ref=Ref,
        Hyp=Hyp,
        withcontext=withcontext,
        validLabels=validLabels,
        tolerance=tolerance,
        endfile=endfile,
    )

    return error_analysis
