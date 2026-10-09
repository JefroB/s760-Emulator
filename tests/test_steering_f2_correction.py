"""
test_steering_f2_correction.py — tests for the steering-doc F2 correction
(mame-live-backend task 12.2).

Task 12.1 corrected the stale "IC20 BOOT ROM undumped (F2)" finding across the
three workspace steering files. These tests read those three files from disk and
assert the correction stuck, covering Requirements 9.1-9.5.

The three files, and their role in the correction:
  * .kiro/steering/reverse-engineering-workflow.md
        This is the ONE file that actually carried the stale STANCE
        ("Emulation (blocked on BOOT ROM) ... needs the BOOT ROM (IC20) dump to
        run ... Until IC20 is dumped"). It was CORRECTED IN PLACE: the stale
        stance markers were rewritten to cite the driver code evidence, F2-REVISED
        was recorded, the ui-consolidation F2/F4 cross-reference was added, and the
        empirical-verification caveat was retained.
  * .kiro/steering/s760-hardware.md
  * .kiro/steering/product.md
        Neither of these carried the stale stance. Each had a clearly-marked
        "## F2-REVISED (mame-live-backend)" section ADDED, including the same code
        evidence / cross-reference / caveat PLUS an explicit missing-claim report
        note stating the file did NOT previously carry the stale claim (R9.5).

Note the verbatim string
"MAME cannot cold-boot the OS because the IC20 BOOT ROM is undumped (F2)"
is quoted (inside the missing-claim notes) as the claim being discussed, so the
R9.1 "stale claim gone" assertions key on the STANCE markers that asserted the
blocker as a live claim, not on that quoted phrase.

Host-side only; reads text files, launches no MAME binary (Requirement 8.5).
`pytest tests` from the repo root is how CI runs these.
"""
import os

# repo root = parent of the tests/ directory (same convention as conftest.py)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEERING = os.path.join(ROOT, ".kiro", "steering")

RE_WORKFLOW = os.path.join(STEERING, "reverse-engineering-workflow.md")
HARDWARE = os.path.join(STEERING, "s760-hardware.md")
PRODUCT = os.path.join(STEERING, "product.md")

# The three corrected files.
ALL_FILES = [RE_WORKFLOW, HARDWARE, PRODUCT]

# The file that carried the stale stance and was corrected in place.
STANCE_FILE = RE_WORKFLOW

# The files that did NOT carry the stale stance and instead carry the
# missing-claim report (R9.5).
MISSING_CLAIM_FILES = [HARDWARE, PRODUCT]

# Stance markers that, if present as LIVE (uncorrected) assertions, would mean the
# stale "MAME is blocked until IC20 is dumped" claim still stands. These are the
# exact fragments the old reverse-engineering-workflow.md carried.
STALE_STANCE_MARKERS = [
    "blocked on BOOT ROM",
    "needs the BOOT ROM (IC20) dump to run",
    "Until IC20 is dumped",
    "MAME can't run until the IC20 BOOT ROM is dumped",
]


def _read(path):
    assert os.path.exists(path), f"steering file missing: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# R9.1 — stale claim replaced with code evidence
# ---------------------------------------------------------------------------

def test_r91_stale_stance_markers_absent_as_live_claims():
    """R9.1: none of the three files assert the stale 'blocked until IC20
    dumped' stance any longer."""
    for path in ALL_FILES:
        text = _read(path)
        for marker in STALE_STANCE_MARKERS:
            assert marker not in text, (
                f"R9.1 FAILED: stale stance marker {marker!r} still present as a "
                f"live claim in {os.path.basename(path)}; it should have been "
                f"rewritten/removed by the F2 correction."
            )


def test_r91_code_evidence_present_in_each_file():
    """R9.1: each file cites the driver code evidence that replaces the stale
    claim (generic MCS-96 core, disk image as program region, address map)."""
    for path in ALL_FILES:
        text = _read(path)
        base = os.path.basename(path)
        assert "N8097BH" in text, (
            f"R9.1 FAILED: {base} missing the N8097BH generic-MCS-96-core code "
            f"evidence."
        )
        assert "s760224.img" in text, (
            f"R9.1 FAILED: {base} missing the s760224.img program-region evidence."
        )
        assert ("ROM_REGION16_LE" in text or "ROM_LOAD" in text), (
            f"R9.1 FAILED: {base} missing the ROM region/load code evidence "
            f"(ROM_REGION16_LE / ROM_LOAD)."
        )
        assert ("map(0x2080" in text and "0x4800" in text), (
            f"R9.1 FAILED: {base} missing the address-map evidence "
            f"(map(0x2080, 0xDFFF) ... region maincpu 0x4800)."
        )


# ---------------------------------------------------------------------------
# R9.2 — F2-REVISED recorded (boots from disk image via N8097BH + s760_mem)
# ---------------------------------------------------------------------------

def test_r92_f2_revised_recorded_in_each_file():
    """R9.2: each file records the F2-REVISED finding with its substance."""
    for path in ALL_FILES:
        text = _read(path)
        base = os.path.basename(path)
        assert "F2-REVISED" in text, (
            f"R9.2 FAILED: {base} does not record the 'F2-REVISED' marker."
        )
        lower = text.lower()
        assert "boots" in lower, (
            f"R9.2 FAILED: {base} F2-REVISED finding does not state the OS 'boots' "
            f"from the disk image."
        )
        assert "s760224.img" in text, (
            f"R9.2 FAILED: {base} F2-REVISED finding does not name the s760224.img "
            f"disk image."
        )
        assert "N8097BH" in text, (
            f"R9.2 FAILED: {base} F2-REVISED finding does not name the N8097BH core."
        )
        assert ("s760_mem" in text or "address map" in lower), (
            f"R9.2 FAILED: {base} F2-REVISED finding does not reference the "
            f"s760_mem address map."
        )


# ---------------------------------------------------------------------------
# R9.3 — ui-consolidation cross-reference present (F2/F4 superseded)
# ---------------------------------------------------------------------------

def test_r93_ui_consolidation_cross_reference_present():
    """R9.3: each file cross-references the ui-consolidation spec's F2/F4
    findings and marks them superseded."""
    for path in ALL_FILES:
        text = _read(path)
        lower = text.lower()
        base = os.path.basename(path)
        assert "ui-consolidation" in text, (
            f"R9.3 FAILED: {base} missing the 'ui-consolidation' cross-reference."
        )
        assert ("f2/f4" in lower or ("f2" in lower and "f4" in lower)), (
            f"R9.3 FAILED: {base} does not reference the ui-consolidation F2/F4 "
            f"findings."
        )
        assert "supersed" in lower, (
            f"R9.3 FAILED: {base} does not state the ui-consolidation artifacts "
            f"are superseded (no 'supersed...' token)."
        )


# ---------------------------------------------------------------------------
# R9.4 — empirical-verification caveat retained (tied to Requirement 2)
# ---------------------------------------------------------------------------

def test_r94_empirical_verification_caveat_retained():
    """R9.4: each file keeps the empirical-verification caveat tying the claim
    to mame-live-backend Requirement 2 and its signals/harness."""
    for path in ALL_FILES:
        text = _read(path)
        lower = text.lower()
        base = os.path.basename(path)
        assert "empiric" in lower, (
            f"R9.4 FAILED: {base} missing the empirical-verification caveat "
            f"(no 'empiric...' token)."
        )
        assert "Requirement 2" in text, (
            f"R9.4 FAILED: {base} empirical caveat does not tie to Requirement 2."
        )
        assert ("m_vdp_vram_active" in text or "vdp_vram_active" in text), (
            f"R9.4 FAILED: {base} empirical caveat does not reference the VRAM "
            f"activity signal (m_vdp_vram_active / vdp_vram_active)."
        )
        assert "tests/mame_harness.py" in text, (
            f"R9.4 FAILED: {base} empirical caveat does not reference "
            f"tests/mame_harness.py."
        )


# ---------------------------------------------------------------------------
# R9.5 — missing-claim report for files that didn't carry the stale claim
# ---------------------------------------------------------------------------

def test_r95_missing_claim_report_in_non_stance_files():
    """R9.5: s760-hardware.md and product.md explicitly report that they did
    NOT previously carry the stale claim."""
    for path in MISSING_CLAIM_FILES:
        text = _read(path)
        lower = text.lower()
        base = os.path.basename(path)
        reported = (
            "did not previously carry" in lower
            or "did not contain the stale" in lower
            or "did not previously contain" in lower
        )
        assert reported, (
            f"R9.5 FAILED: {base} did not carry the stale stance, so it must "
            f"explicitly report that it 'did not previously carry' / 'did not "
            f"contain the stale' claim; no such note found."
        )


def test_r95_stance_file_corrected_in_place_not_missing_claim():
    """R9.5 (companion): reverse-engineering-workflow.md is the file that
    carried the stance and was corrected in place. It should NOT claim it lacked
    the stale stance, and it must show the stance was rewritten to STALE/corrected
    rather than reported as absent."""
    text = _read(STANCE_FILE)
    lower = text.lower()
    # It carried the stance, so it must NOT report 'did not previously carry'.
    assert "did not previously carry" not in lower, (
        "R9.5 FAILED: reverse-engineering-workflow.md carried the stale stance "
        "and was corrected in place; it must not use the missing-claim report "
        "phrasing reserved for the files that lacked the claim."
    )
    # The in-place correction labels the old stance as stale/corrected.
    assert "stale" in lower and "corrected" in lower, (
        "R9.5 FAILED: reverse-engineering-workflow.md should mark its former "
        "stance as STALE and corrected (in-place correction)."
    )
