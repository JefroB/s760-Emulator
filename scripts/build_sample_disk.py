#!/usr/bin/env python3
"""build_sample_disk.py — reusable, fully-configurable Roland S-760 sample-disk builder.

Builds an OS-loadable 720 KB (737,280-byte) S-760 sample disk image by editing a
preserved, byte-exact template (`roms/FDD/waves760.sdk`) in place on a COPY and
overwriting the Volume / Performance / Patch / Partial / Sample / PCM records at
their decoded fixed offsets.

Ground truth: this reproduces the exact byte layout used by ChatGPT's working,
OS-verified builders (build_robo_tvf_81.py, prepare_loops_102.py,
prepare_static_107.py, prepare_pitch_109.py). Offsets are stable across all of
those builds. See `.agents/skills/s760-fdd-sample-disk/SKILL.md`.

DESIGN GOALS
------------
* **Nothing hardcoded.** Performance name, volume name, and EVERY patch / partial
  / sample / PCM field is a configurable parameter supplied via a declarative
  spec (a Python dict or a JSON file). The spec library at the bottom shows how
  to drive it; `--spec file.json` loads one from disk.
* **Non-destructive.** The template is opened read-only; output is a new file.
  Size is asserted == 737280 and the template header is asserted intact.
* **Synth-friendly.** Built-in single-cycle waveform generators (sine, saw,
  square, triangle, pulse, noise) plus arbitrary custom sample arrays and WAV
  file import, so you can use the S-760 as a synthesizer from single cycles.
* **Reproducible.** Writes a manifest JSON (sizes + SHA256 of template & output,
  plus the resolved spec) next to the image.

OFFSET MAP (file offsets, hex) — all CONFIRMED against the working builders
---------------------------------------------------------------------------
  0x1200              Volume name (16 bytes, space-padded ASCII)
  0x4E04              Performance name (12 bytes). Byte at 0x4E07 (mode) preserved.
  0x1600 + 16*i       Patch catalog name (16 bytes), i = patch index
  0x8E00 + 256*i      Patch record (256 bytes):
                        +0x00  name (16 bytes)
                        +0x10  index (1 byte)
                        +0x20..+0x78  88-key -> partial-index map (MIDI 21..108)
                        +0xD0..+0x100 pitch/mod/aftertouch/TVF patch offsets
                                      (48 bytes; zero them to disable patch-level
                                       pitch/controller contributions)
  0x1E00 + 16*i       Partial catalog name (16 bytes)
  0x10E00 + 128*i     Partial record (128 bytes):
                        +0x00  name (16 bytes)
                        +0x10  index (u16 LE)
                        +0x15  coarse tune (signed semitones, int8)
                        +0x4B  TVF mode (0=LPF, 1=BPF, 2=HPF, 255=bypass)
                        +0x4C  TVF cutoff (0..127)
                        +0x4D  TVF resonance (0..127)
                        +0x4F..+0x52 TVA/velocity sens triplet [a,b,vel_sens]
                        +0x52..+0x56 TVF envelope levels [l1,l2,l3,l4]
                        +0x56..+0x5A TVF envelope times [t1,t2,t3,t4]
                        +0x5A  TVF envelope depth
                        +0x5B..+0x60 secondary envelope [0,60,0,0,0] default
                        +0x61..+0x63 TVA velocity/time sens (2 bytes)
                        +0x6A  TVA sustain-ish constant (=20 in refs)
                        +0x75..+0x7B LFO depths (6 bytes)
  0x2E00 + 16*i       Sample catalog name (16 bytes)
  0x18E00 + (i//10)*512 + (i%10)*48   Sample record (48 bytes, 10 per 512B sector):
                        +0x00  name (16 bytes)
                        +0x10  5 x u32 LE: start, loop start, loop end,
                               release-loop start, release-loop end (each <<8)
                        +0x24  loop mode (0=forward, 2=one shot); +0x25..27 zero
                        +0x28  cluster (u16 LE) = i + 5
                        +0x2A  clusters (u16 LE) = 1
                        +0x2C  sample-rate code (0=48k, 1=44.1k; see SAMPLE_RATES)
                        +0x2D  root key (1 byte, MIDI note)
  0x2AC00 + i*0x2400  PCM data slot (0x2400 bytes = 4608 int16 LE = 4096 waveform
                                      + 512 wrap-padding samples)

MIDI selection: a note's patch is chosen by MIDI program_change = patch index i.
Within a patch, the played MIDI key (21..108) selects the partial via the key map.

Usage
-----
  python scripts/build_sample_disk.py --preset demo-synth --out roms/FDD/MYSYNTH.IMG
  python scripts/build_sample_disk.py --spec my_spec.json --out roms/FDD/CUSTOM.IMG
  python scripts/build_sample_disk.py --list-presets
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants (byte-exact; do not change without re-verifying against the OS)
# ---------------------------------------------------------------------------
IMAGE_SIZE = 737280
TEMPLATE_TAG = b'S770 MR25A'
TEMPLATE_HEADER = (1, 22, 23, 23)   # <4H at 0x108

OFF_VOLUME_NAME = 0x1200
OFF_PERF_NAME = 0x4E04              # 12-byte perf name; mode byte at +3 preserved
PERF_NAME_LEN = 12

OFF_PATCH_CATALOG = 0x1600         # +16*i
OFF_PATCH_RECORD = 0x8E00          # +256*i, 256 bytes
OFF_PARTIAL_CATALOG = 0x1E00       # +16*i
OFF_PARTIAL_RECORD = 0x10E00       # +128*i, 128 bytes
OFF_SAMPLE_CATALOG = 0x2E00        # +16*i
OFF_SAMPLE_SECTOR = 0x18E00        # (i//10)*512 + (i%10)*48, 48 bytes
OFF_PCM = 0x2AC00                  # +i*0x2400
PCM_SLOT_BYTES = 0x2400            # 4608 int16
PCM_WAVE_SAMPLES = 4096
PCM_WRAP_SAMPLES = 512

# Original OS 001F:71E8 writes this byte; 001F:714C writes loop mode.
SAMPLE_RATES = {48000: 0, 44100: 1, 24000: 2, 22050: 3,
                30000: 4, 15000: 5, 32000: 6, 16000: 7}
LOOP_MODES = {'forward': 0, 'one_shot': 2}
SAMPLE_POINT_FIELDS = ('start', 'loop_start', 'loop_end', 'release_start', 'release_end')

MIDI_KEY_LO = 21                   # first key covered by the 88-key map (0x20)
MIDI_KEY_HI = 108                  # last key (inclusive) -> 88 entries

# TVF mode names
TVF_MODES = {'lpf': 0, 'lp': 0, 'bpf': 1, 'bp': 1, 'hpf': 2, 'hp': 2,
             'bypass': 255, 'off': 255}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _name(s: str, length: int = 16) -> bytes:
    return s.encode('ascii', 'replace').ljust(length, b' ')[:length]


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(v)))


def _resolve_tvf_mode(mode) -> int:
    if isinstance(mode, int):
        return mode & 0xFF
    return TVF_MODES[str(mode).strip().lower()]


# ---------------------------------------------------------------------------
# Single-cycle / waveform generators (synth building blocks)
# ---------------------------------------------------------------------------
def gen_waveform(kind: str, n: int = PCM_WAVE_SAMPLES, amp: int = 8192,
                 cycles: int = 1, duty: float = 0.5, seed: int = 1234,
                 harmonics: int | None = None) -> list[int]:
    """Generate a single-cycle (or multi-cycle) int16 waveform of length n.

    kind: sine | saw | square | triangle | pulse | noise | ramp_down
    amp:  peak amplitude (<= 32767). cycles: number of periods across n samples.
    duty: pulse/square duty (0..1). harmonics: band-limit cap for saw/square.
    """
    kind = kind.lower()
    out = []
    if kind == 'sine':
        for i in range(n):
            out.append(round(amp * math.sin(2 * math.pi * cycles * i / n)))
    elif kind in ('saw', 'ramp_up'):
        for i in range(n):
            phase = (cycles * i / n) % 1.0
            if harmonics:
                v = 0.0
                for h in range(1, harmonics + 1):
                    v += math.sin(2 * math.pi * h * phase) / h
                out.append(round(amp * (2 / math.pi) * v))
            else:
                out.append(round(amp * (2 * phase - 1)))
    elif kind == 'ramp_down':
        for i in range(n):
            phase = (cycles * i / n) % 1.0
            out.append(round(amp * (1 - 2 * phase)))
    elif kind in ('square', 'pulse'):
        for i in range(n):
            phase = (cycles * i / n) % 1.0
            out.append(amp if phase < duty else -amp)
    elif kind == 'triangle':
        for i in range(n):
            phase = (cycles * i / n) % 1.0
            tri = 1 - 4 * abs(phase - 0.5)
            out.append(round(amp * tri))
    elif kind == 'noise':
        import random
        rng = random.Random(seed)
        out = [rng.randint(-amp, amp) for _ in range(n)]
    else:
        raise ValueError(f'unknown waveform kind: {kind!r}')
    return out


def load_wav_mono(path: str, n: int = PCM_WAVE_SAMPLES) -> list[int]:
    """Load a mono 16-bit WAV, truncate/zero-pad to n samples."""
    import wave
    with wave.open(path, 'rb') as w:
        if w.getsampwidth() != 2:
            raise ValueError('WAV must be 16-bit PCM')
        frames = w.readframes(w.getnframes())
        ch = w.getnchannels()
        data = list(struct.unpack('<%dh' % (len(frames) // 2), frames))
        if ch > 1:
            data = data[::ch]  # take channel 0
    if len(data) >= n:
        return data[:n]
    return data + [0] * (n - len(data))


def _resolve_pcm(sample_spec: dict) -> list[int]:
    """Return a 4096-sample int16 waveform from a sample spec's `pcm` field.

    pcm forms:
      {"waveform": "sine", "amp": 8192, "cycles": 1, ...}  -> generated
      {"wav": "path/to/file.wav"}                           -> imported
      {"samples": [ ... ints ... ]}                         -> literal
      (absent)                                              -> silence
    """
    pcm = sample_spec.get('pcm')
    if pcm is None:
        return [0] * PCM_WAVE_SAMPLES
    if 'samples' in pcm:
        data = list(pcm['samples'])[:PCM_WAVE_SAMPLES]
        return data + [0] * (PCM_WAVE_SAMPLES - len(data))
    if 'wav' in pcm:
        return load_wav_mono(pcm['wav'])
    if 'waveform' in pcm:
        kw = {k: v for k, v in pcm.items() if k != 'waveform'}
        return gen_waveform(pcm['waveform'], **kw)
    raise ValueError(f'unrecognized pcm spec: {pcm!r}')


# ---------------------------------------------------------------------------
# Record writers
# ---------------------------------------------------------------------------
def _write_patch(d: bytearray, template: bytes, i: int, patch: dict):
    base = OFF_PATCH_RECORD + 256 * i
    rec = bytearray(template[OFF_PATCH_RECORD:OFF_PATCH_RECORD + 256])
    name = _name(patch.get('name', f'PATCH {i + 1:02}'))
    rec[0:16] = name
    rec[0x10] = i & 0xFF

    # 88-key -> partial map (MIDI 21..108). Default: all keys -> partial `i`
    # unless an explicit key_map is given.
    key_map = patch.get('key_map')
    if key_map is None:
        default_partial = patch.get('partial', i) & 0xFF
        rec[0x20:0x78] = bytes([default_partial]) * 88
    else:
        km = bytearray(88)
        # key_map: {midi_key: partial_index} OR list of 88 partial indices
        if isinstance(key_map, dict):
            for k, p in key_map.items():
                k = int(k)
                if MIDI_KEY_LO <= k <= MIDI_KEY_HI:
                    km[k - MIDI_KEY_LO] = int(p) & 0xFF
        else:
            for idx, p in enumerate(key_map[:88]):
                km[idx] = int(p) & 0xFF
        rec[0x20:0x78] = bytes(km)

    # Patch-level pitch/mod/aftertouch/TVF offsets (0xD0..0x100). Zero disables.
    patch_offsets = patch.get('patch_offsets')
    if patch_offsets is None:
        rec[0xD0:0x100] = bytes(48)
    else:
        po = bytes(patch_offsets)[:48].ljust(48, b'\x00')
        rec[0xD0:0x100] = po

    d[base:base + 256] = rec
    d[OFF_PATCH_CATALOG + 16 * i:OFF_PATCH_CATALOG + 16 * i + 16] = name


def _write_partial(d: bytearray, template: bytes, i: int, partial: dict):
    base = OFF_PARTIAL_RECORD + 128 * i
    rec = bytearray(template[OFF_PARTIAL_RECORD:OFF_PARTIAL_RECORD + 128])
    name = _name(partial.get('name', f'PARTIAL {i + 1:02}'))
    rec[0:16] = name
    struct.pack_into('<H', rec, 0x10, i)

    rec[0x15] = partial.get('coarse_tune', 0) & 0xFF        # signed semitones

    rec[0x4B] = _resolve_tvf_mode(partial.get('tvf_mode', 'bypass'))
    rec[0x4C] = _clamp(partial.get('cutoff', 127), 0, 127)
    rec[0x4D] = _clamp(partial.get('resonance', 0), 0, 127)

    # TVA / velocity sensitivity triplet @0x4F..0x52
    vsens = partial.get('velocity_sens', 0)
    tri = partial.get('tva_sens_triplet', [0, 0, vsens])
    rec[0x4F:0x52] = bytes(_clamp(x, 0, 255) for x in tri[:3])

    # TVF envelope. Defaults mirror the reference builders:
    #   sweep: levels [0,127,0,0], times [80,80,1,20], depth63
    #   static: levels [0,127,127,127], times [0,1,1,20], depth0
    # Explicit API rates means the Time column. BUG-073 corrected byte mapping;
    # implicit legacy presets retain their established byte layouts.
    env = partial.get('tvf_env')
    if env is None:
        if partial.get('sweep'):
            rec[0x52:0x56] = bytes([0, 127, 0, 0])
            rec[0x56:0x5A] = bytes([80, 80, 1, 20])
            rec[0x5A] = 63
        else:
            rec[0x52:0x56] = bytes([0, 127, 127, 127])
            rec[0x56:0x5A] = bytes([0, 1, 1, 20])
            rec[0x5A] = 0
    else:
        rec[0x52:0x56] = bytes(x & 0xFF for x in env.get('levels', [0, 127, 127, 127])[:4])
        rec[0x56:0x5A] = bytes(x & 0xFF for x in env.get('rates', [0, 1, 1, 20])[:4])
        rec[0x5A] = env.get('depth', 0) & 0xFF

    sec = partial.get('secondary_env', [0, 60, 0, 0, 0])
    rec[0x5B:0x60] = bytes(x & 0xFF for x in sec[:5])

    tva = partial.get('tva_sens', [0, 0])
    rec[0x61:0x63] = bytes(x & 0xFF for x in tva[:2])
    rec[0x6A] = partial.get('tva_sustain', 20) & 0xFF

    lfo = partial.get('lfo_depths', [0, 0, 0, 0, 0, 0])
    rec[0x75:0x7B] = bytes(x & 0xFF for x in lfo[:6])

    d[base:base + 128] = rec
    d[OFF_PARTIAL_CATALOG + 16 * i:OFF_PARTIAL_CATALOG + 16 * i + 16] = name


def _write_sample(d: bytearray, template: bytes, i: int, sample: dict):
    # loop_enable was historically misnamed: it wrote the rate code. Preserve
    # those bytes for existing fixture specs, but require new specs to use Hz.
    if 'sample_rate' in sample:
        rate = sample['sample_rate']
        if 'loop_enable' in sample:
            raise ValueError('Use sample_rate or legacy loop_enable, not both')
        if type(rate) is not int or rate not in SAMPLE_RATES:
            raise ValueError(f'Unsupported sample_rate: {rate!r}')
        rate_code = SAMPLE_RATES[rate]
    else:
        rate_code = sample.get('loop_enable', 0) & 0xFF
    mode = sample.get('loop_mode', 'forward')
    if not isinstance(mode, str) or mode not in LOOP_MODES:
        raise ValueError(f'Unsupported loop_mode: {mode!r}')

    if 'sample_points' in sample:
        points = sample['sample_points']
        if any(key in sample for key in ('start', 'end', 'loop_start', 'loop_end')):
            raise ValueError('Do not mix sample_points with legacy address fields')
        if not isinstance(points, dict) or set(points) != set(SAMPLE_POINT_FIELDS):
            raise ValueError(f'sample_points requires exactly {SAMPLE_POINT_FIELDS}')
        addresses = [points[key] for key in SAMPLE_POINT_FIELDS]
        if any(type(value) is not int or not 0 <= value < PCM_SLOT_BYTES // 2
               for value in addresses):
            raise ValueError('sample_points must be integer offsets within the PCM slot')
    else:
        # Historical API labels were shifted by one field. Retain its bytes;
        # explicit native points belong in sample_points above.
        addresses = [0, sample.get('start', 0), sample.get('loop_start', 0),
                     sample.get('loop_end', PCM_WAVE_SAMPLES),
                     sample.get('end', PCM_WAVE_SAMPLES)]

    so = OFF_SAMPLE_SECTOR + (i // 10) * 512 + (i % 10) * 48
    rec = bytearray(template[so:so + 48])
    name = _name(sample.get('name', f'SAMPLE {i + 1:02}'))
    rec[0:16] = name

    struct.pack_into('<5I', rec, 16, *(value << 8 for value in addresses))
    rec[0x24:0x28] = bytes(4)
    rec[0x24] = LOOP_MODES[mode]
    # Cluster layout: PCM slot i lives at cluster i+5, one cluster long.
    struct.pack_into('<H', rec, 0x28, i + 5)
    struct.pack_into('<H', rec, 0x2A, 1)
    rec[0x2C] = rate_code
    rec[0x2D] = _clamp(sample.get('root_key', 60), 0, 127)

    d[so:so + 48] = rec
    d[OFF_SAMPLE_CATALOG + 16 * i:OFF_SAMPLE_CATALOG + 16 * i + 16] = name

    # PCM payload: 4096 waveform + 512 wrap-padding (= first 512 of waveform).
    wave = _resolve_pcm(sample)
    wave = wave[:PCM_WAVE_SAMPLES] + [0] * (PCM_WAVE_SAMPLES - len(wave))
    padded = wave + [wave[j % PCM_WAVE_SAMPLES] for j in range(PCM_WRAP_SAMPLES)]
    payload = struct.pack('<%dh' % len(padded),
                          *(_clamp(v, -32768, 32767) for v in padded))
    off = OFF_PCM + i * PCM_SLOT_BYTES
    d[off:off + PCM_SLOT_BYTES] = payload
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(spec: dict, template_path: Path, out_path: Path,
          manifest_path: Path | None = None) -> dict:
    if template_path.resolve() == out_path.resolve():
        raise ValueError('Template must remain immutable')
    template = template_path.read_bytes()
    if len(template) != IMAGE_SIZE:
        raise SystemExit(f'template size {len(template)} != {IMAGE_SIZE}')
    if template[4:14] != TEMPLATE_TAG:
        raise SystemExit(f'template tag mismatch: {template[4:14]!r}')
    if struct.unpack_from('<4H', template, 0x108) != TEMPLATE_HEADER:
        raise SystemExit('template header (0x108) mismatch')

    d = bytearray(template)

    # Volume + performance names (perf mode byte at 0x4E07 preserved).
    d[OFF_VOLUME_NAME:OFF_VOLUME_NAME + 16] = _name(spec.get('volume_name', 'VOLUME'))
    perf = _name(spec.get('performance_name', 'PERFORMANCE'), PERF_NAME_LEN)
    d[OFF_PERF_NAME:OFF_PERF_NAME + PERF_NAME_LEN] = perf

    patches = spec.get('patches', [])
    partials = spec.get('partials', [])
    samples = spec.get('samples', [])

    for i, p in enumerate(patches):
        _write_patch(d, template, i, p)
    for i, p in enumerate(partials):
        _write_partial(d, template, i, p)

    pcm_hashes = []
    for i, s in enumerate(samples):
        pcm_hashes.append(_write_sample(d, template, i, s))

    if len(d) != IMAGE_SIZE:
        raise SystemExit(f'built image size {len(d)} != {IMAGE_SIZE}')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(d)

    manifest = {
        'image': str(out_path),
        'size': len(d),
        'sha256': hashlib.sha256(d).hexdigest(),
        'template': str(template_path),
        'template_sha256': hashlib.sha256(template).hexdigest(),
        'volume_name': spec.get('volume_name', 'VOLUME'),
        'performance_name': spec.get('performance_name', 'PERFORMANCE'),
        'counts': {'patches': len(patches), 'partials': len(partials),
                   'samples': len(samples)},
        'pcm_sha256': pcm_hashes,
        'tvf_envelope_layout': 'partial+0x52 levels; partial+0x56 times (API rates)',
        'spec': spec,
    }
    if manifest_path is None:
        manifest_path = out_path.with_suffix(out_path.suffix + '.manifest.json')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


# ---------------------------------------------------------------------------
# Preset spec library (examples — fully data-driven, copy & edit freely)
# ---------------------------------------------------------------------------
def preset_demo_synth() -> dict:
    """Four single-cycle oscillators as four MIDI programs, open LPF, looped.

    Each sample loops its single cycle so a held key sustains indefinitely —
    turning the S-760 into a basic subtractive-synth oscillator bank.
    """
    waves = [('SINE', 'sine', {}),
             ('SAW', 'saw', {'harmonics': 64}),
             ('SQUARE', 'square', {'duty': 0.5}),
             ('PULSE 25', 'pulse', {'duty': 0.25})]
    patches, partials, samples = [], [], []
    for i, (label, kind, kw) in enumerate(waves):
        patches.append({'name': f'{i + 1:02} {label}', 'partial': i})
        partials.append({
            'name': f'{i + 1:02} {label}',
            'tvf_mode': 'lpf', 'cutoff': 110, 'resonance': 20,
            'sweep': False,
            'lfo_depths': [0, 0, 0, 0, 0, 0],
        })
        samples.append({
            'name': f'{i + 1:02} {label}',
            'root_key': 60,
            'start': 0, 'end': 4096,
            'loop_start': 0, 'loop_end': 4096,
            'sample_rate': 44100, 'loop_mode': 'forward',
            'pcm': dict(waveform=kind, amp=8192, cycles=1, **kw),
        })
    return {
        'volume_name': 'DEMO SYNTH',
        'performance_name': 'DEMO SYNTH',
        'patches': patches, 'partials': partials, 'samples': samples,
    }


def preset_filter_sweep() -> dict:
    """One saw oscillator with a resonant LPF envelope sweep (classic synth lead)."""
    return {
        'volume_name': 'SWEEP LEAD',
        'performance_name': 'SWEEP LEAD',
        'patches': [{'name': '01 SWEEP SAW', 'partial': 0}],
        'partials': [{
            'name': '01 SWEEP SAW',
            'tvf_mode': 'lpf', 'cutoff': 0, 'resonance': 96,
            'sweep': True,          # uses the sweep envelope defaults
        }],
        'samples': [{
            'name': '01 SWEEP SAW', 'root_key': 60,
            'start': 0, 'end': 4096,
            'loop_start': 0, 'loop_end': 4096,
            'sample_rate': 44100, 'loop_mode': 'forward',
            'pcm': {'waveform': 'saw', 'amp': 10000, 'cycles': 1, 'harmonics': 96},
        }],
    }


PRESETS = {
    'demo-synth': preset_demo_synth,
    'filter-sweep': preset_filter_sweep,
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    repo = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--spec', help='path to a JSON disk spec')
    ap.add_argument('--preset', help='named built-in preset spec')
    ap.add_argument('--list-presets', action='store_true')
    ap.add_argument('--template', default=str(repo / 'roms/FDD/waves760.sdk'),
                    help='OS-loadable template (default roms/FDD/waves760.sdk)')
    ap.add_argument('--out', help='output .IMG path')
    ap.add_argument('--manifest', help='manifest JSON path (default <out>.manifest.json)')
    args = ap.parse_args(argv)

    if args.list_presets:
        print('Available presets:')
        for k in PRESETS:
            print('  ', k)
        return 0

    if args.spec:
        spec = json.loads(Path(args.spec).read_text())
    elif args.preset:
        if args.preset not in PRESETS:
            ap.error(f'unknown preset {args.preset!r}; see --list-presets')
        spec = PRESETS[args.preset]()
    else:
        ap.error('provide --spec FILE or --preset NAME (or --list-presets)')

    if not args.out:
        ap.error('--out is required')

    manifest = build(spec, Path(args.template), Path(args.out),
                     Path(args.manifest) if args.manifest else None)
    print('built', manifest['image'])
    print('size ', manifest['size'])
    print('sha256', manifest['sha256'])
    print('counts', manifest['counts'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
