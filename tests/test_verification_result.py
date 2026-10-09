"""
test_verification_result.py — unit tests for the OS-execution verification
pass / skip / gap predicate (mame-live-backend task 10.3).

These tests exercise the PURE `classify_verification` predicate (plus the
`make_signals` helper and `VerificationResult.to_dict()` serializer) in
`tests/mame_harness.py`. They launch NO MAME binary — the predicate performs no
I/O, so the pass/skip/gap decision is verifiable on any host (Requirement 8.5).

Requirement coverage:
  2.2 — each execution signal is recorded with its originating controller.
  2.3 — pass requires >=1 signal true AND a captured CRT frame with
        nonBackgroundPixels > 0.
  2.4 — artifacts absent -> skipped, never pass/fail.
  2.5 — bounded run elapsed with neither signal true -> explicit gap finding
        naming the false signals; a captured frame is NOT reported as a pass.

Imported the same way the existing tests in tests/ import the harness
(`from mame_harness import ...`); `pytest tests` from the repo root puts the
tests/ directory on sys.path via its conftest.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from mame_harness import (  # noqa: E402
    VerificationResult,
    classify_verification,
    make_signals,
    VDP_SIGNAL_SOURCE,
    SED_SIGNAL_SOURCE,
    DEFAULT_VERIFICATION_DURATION_SEC,
)


# A genuine captured CRT frame with real (non-background) content.
_GOOD_FRAME = {"captured": True, "nonBackgroundPixels": 12345}


# ---------------------------------------------------------------------------
# 1. pass: VDP signal true + a captured frame with non-background pixels (R2.3)
# ---------------------------------------------------------------------------
def test_pass_via_vdp_signal_with_genuine_frame():
    signals = make_signals(vdp_active=True, sed_active=False)
    result = classify_verification(
        signals=signals,
        crt_frame=_GOOD_FRAME,
        artifacts_present=True,
        duration_elapsed=True,
    )
    assert result.status == "pass"
    assert result.gap_finding is None
    # R2.2: each signal carries its originating controller string.
    assert result.signals["vdpVramActive"]["source"] == VDP_SIGNAL_SOURCE
    assert result.signals["sedVramActive"]["source"] == SED_SIGNAL_SOURCE
    assert result.signals["vdpVramActive"]["value"] is True
    # The captured frame is echoed back on the result unchanged.
    assert result.crt_frame == _GOOD_FRAME


# ---------------------------------------------------------------------------
# 2. pass via the OTHER signal: SED true + captured frame with pixels (R2.3)
# ---------------------------------------------------------------------------
def test_pass_via_sed_signal_with_genuine_frame():
    signals = make_signals(vdp_active=False, sed_active=True)
    result = classify_verification(
        signals=signals,
        crt_frame={"captured": True, "nonBackgroundPixels": 1},
        artifacts_present=True,
        duration_elapsed=True,
    )
    assert result.status == "pass"
    assert result.gap_finding is None
    assert result.signals["sedVramActive"]["value"] is True


# ---------------------------------------------------------------------------
# 3. skipped: artifacts absent -> never pass/fail, crtFrame None (R2.4)
# ---------------------------------------------------------------------------
def test_skipped_when_artifacts_absent():
    # Even with signals true and a good frame, absent artifacts => skipped.
    signals = make_signals(vdp_active=True, sed_active=True)
    result = classify_verification(
        signals=signals,
        crt_frame=_GOOD_FRAME,
        artifacts_present=False,
        duration_elapsed=False,
        skip_reason="MAME binary not found",
    )
    assert result.status == "skipped"
    assert result.status not in ("pass", "fail")
    assert result.skip_reason is not None
    assert result.crt_frame is None
    assert result.gap_finding is None


def test_skipped_has_default_reason_when_none_supplied():
    result = classify_verification(
        signals=make_signals(False, False),
        crt_frame=None,
        artifacts_present=False,
        duration_elapsed=False,
    )
    assert result.status == "skipped"
    assert result.skip_reason  # non-empty default reason


# ---------------------------------------------------------------------------
# 4. gap: both signals false after the bounded duration -> fail + gap finding
#    naming BOTH signals; a captured frame is NOT reported as a pass (R2.5)
# ---------------------------------------------------------------------------
def test_gap_both_signals_false_is_fail_not_pass():
    signals = make_signals(vdp_active=False, sed_active=False)
    # A frame WAS captured with real pixels, but neither signal is true: the
    # frame must NOT be reported as a pass (R2.5).
    result = classify_verification(
        signals=signals,
        crt_frame=_GOOD_FRAME,
        artifacts_present=True,
        duration_elapsed=True,
    )
    assert result.status == "fail"
    assert result.status != "pass"
    assert isinstance(result.gap_finding, str)
    assert result.gap_finding  # non-empty
    # The gap finding names BOTH signals that stayed false.
    assert "vdpVramActive" in result.gap_finding
    assert "sedVramActive" in result.gap_finding


def test_gap_not_reported_before_duration_elapses():
    # Same false/false signals but the run has NOT yet elapsed: no gap finding.
    result = classify_verification(
        signals=make_signals(False, False),
        crt_frame=None,
        artifacts_present=True,
        duration_elapsed=False,
    )
    assert result.status == "fail"
    assert result.gap_finding is None


# ---------------------------------------------------------------------------
# 5. fail: a signal is true but no genuine frame -> fail, gap_finding None
#    (a signal was true, so this is not a boot/display gap)
# ---------------------------------------------------------------------------
def test_fail_signal_true_but_no_frame_captured():
    result = classify_verification(
        signals=make_signals(vdp_active=True, sed_active=False),
        crt_frame=None,
        artifacts_present=True,
        duration_elapsed=True,
    )
    assert result.status == "fail"
    # A signal was true => not a gap, so no gap finding.
    assert result.gap_finding is None


def test_fail_signal_true_but_frame_has_zero_pixels():
    result = classify_verification(
        signals=make_signals(vdp_active=True, sed_active=False),
        crt_frame={"captured": True, "nonBackgroundPixels": 0},
        artifacts_present=True,
        duration_elapsed=True,
    )
    assert result.status == "fail"
    assert result.gap_finding is None


# ---------------------------------------------------------------------------
# 6. R2.2 source labels: make_signals produces non-empty controller strings and
#    classify_verification preserves them in result.signals.
# ---------------------------------------------------------------------------
def test_make_signals_carries_controller_source_labels():
    signals = make_signals(vdp_active=True, sed_active=False)
    assert signals["vdpVramActive"]["source"] == VDP_SIGNAL_SOURCE
    assert signals["sedVramActive"]["source"] == SED_SIGNAL_SOURCE
    # Source labels are non-empty controller strings.
    assert isinstance(signals["vdpVramActive"]["source"], str)
    assert signals["vdpVramActive"]["source"].strip()
    assert isinstance(signals["sedVramActive"]["source"], str)
    assert signals["sedVramActive"]["source"].strip()
    # Values reflect the requested flags.
    assert signals["vdpVramActive"]["value"] is True
    assert signals["sedVramActive"]["value"] is False


def test_classify_preserves_source_labels_in_result():
    signals = make_signals(vdp_active=False, sed_active=True)
    result = classify_verification(
        signals=signals,
        crt_frame=_GOOD_FRAME,
        artifacts_present=True,
        duration_elapsed=True,
    )
    assert result.signals["vdpVramActive"]["source"] == VDP_SIGNAL_SOURCE
    assert result.signals["sedVramActive"]["source"] == SED_SIGNAL_SOURCE


# ---------------------------------------------------------------------------
# VerificationResult.to_dict() emits the exact camelCase key set.
# ---------------------------------------------------------------------------
def test_to_dict_emits_exact_camelcase_keys():
    result = classify_verification(
        signals=make_signals(vdp_active=True, sed_active=False),
        crt_frame=_GOOD_FRAME,
        artifacts_present=True,
        duration_elapsed=True,
    )
    d = result.to_dict()
    assert set(d.keys()) == {
        "status",
        "skipReason",
        "durationSec",
        "signals",
        "crtFrame",
        "gapFinding",
    }
    # Values map through correctly.
    assert d["status"] == "pass"
    assert d["skipReason"] is None
    assert d["durationSec"] == DEFAULT_VERIFICATION_DURATION_SEC
    assert d["signals"] == result.signals
    assert d["crtFrame"] == _GOOD_FRAME
    assert d["gapFinding"] is None


def test_to_dict_skipped_shape():
    result = classify_verification(
        signals=make_signals(False, False),
        crt_frame=_GOOD_FRAME,
        artifacts_present=False,
        duration_elapsed=False,
        skip_reason="ROM set absent",
    )
    d = result.to_dict()
    assert d["status"] == "skipped"
    assert d["skipReason"] == "ROM set absent"
    assert d["crtFrame"] is None
    assert d["gapFinding"] is None
