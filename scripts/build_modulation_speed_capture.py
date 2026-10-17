"""Build RoboSampler TVF envelope timing disks; preserves the local template."""
import argparse
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

from build_sample_disk import build

ROOT = Path(__file__).resolve().parents[1]
SURVEY = [0, 1, 2, 4, 8, 12, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88,
          96, 104, 112, 120, 126, 127]


def make_spec(rates, label):
    """Four adjacent keys per setting with full-keyboard control patches."""
    rates = list(rates)
    assert 1 <= len(rates) <= 22
    # Start from the template's 22 patch/23 partial/23 sample layout.
    # All samples are identical, so inherited sample routing cannot change stimulus.
    spec = dict(volume_name=f'CAL:MOD {label}', performance_name=f'MOD {label}',
                patches=[], partials=[], samples=[])
    key_map = [min(i // 4, len(rates) - 1) for i in range(88)]
    spec['patches'].append(dict(name=f'MOD {label} KEYMAP', key_map=key_map))
    # Slot 1 is the mapped survey. Slots 2..22 provide full-keyboard controls;
    # the final setting remains available in the survey when all 22 are used.
    for i in range(1, 22):
        rate_index = min(i - 1, len(rates) - 1)
        spec['patches'].append(dict(name=f'TIME {rates[rate_index]:03} ALLKEYS',
                                    partial=rate_index))
    for i in range(23):
        rate = rates[min(i, len(rates) - 1)]
        spec['partials'].append(dict(
            name=f'TIME {rate:03}', tvf_mode='lpf', cutoff=0, resonance=0,
            tvf_env=dict(levels=[64, 96, 64, 96], rates=[rate]*4, depth=63),
            velocity_sens=0, tva_sens=[0, 0], lfo_depths=[0]*6))
        spec['samples'].append(dict(name=f'CAL:MOD NOISE{i:02}', root_key=60,
            start=0, end=4110, loop_start=4096, loop_end=4106, loop_enable=1,
            pcm=dict(waveform='noise', amp=2048, seed=760215)))
    return spec, key_map


def make_single_spec():
    spec, _ = make_spec(SURVEY, 'ALL')
    original = spec['partials']
    spec['partials'] = []
    for rate in range(128):
        partial = dict(original[0], name=f'TIME {rate:03}')
        partial['tvf_env'] = dict(levels=[64,96,64,96], rates=[rate]*4, depth=63)
        spec['partials'].append(partial)
    patches = [dict(name='01 SURVEY', key_map=[SURVEY[i//4] for i in range(88)])]
    for bank, lo in enumerate(range(0,128,22)):
        patches.append(dict(name=f'{bank+2:02} TIME {lo:03}-{min(lo+21,127):03}',
                            key_map=[min(lo+i//4,127) for i in range(88)]))
    for rate in [0,1,2,8,16,32,48,64,80,88,96,104,112,120,127]:
        patches.append(dict(name=f'TIME {rate:03} ALLKEYS', partial=rate))
    assert len(patches)==22
    spec['patches']=patches
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--pcm-gain', type=int, default=1, choices=range(1,16),
                        help='Exact integer PCM multiplier; 15 gives +23.52dB')
    parser.add_argument('--image-name', default='MODALL.IMG')
    args = parser.parse_args()
    if Path(args.image_name).name != args.image_name or not args.image_name.upper().endswith('.IMG'):
        parser.error('--image-name must be an IMG filename, not a path')
    out = args.out_dir.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error('Use a fresh output directory')
    out.mkdir(parents=True, exist_ok=True)
    template = ROOT / 'roms/FDD/waves760.sdk'
    before = hashlib.sha256(template.read_bytes()).hexdigest()
    banks = [('ALL', list(range(128)))]
    rows = []
    for label, rates in banks:
        spec = make_single_spec()
        if args.pcm_gain != 1:
            spec['volume_name'] = 'CAL:MOD V2 LOUD'
            spec['performance_name'] = 'MOD V2 LOUD'
        image = out / args.image_name
        manifest = build(spec, template, image)
        data = bytearray(image.read_bytes())
        # Existing ROBOFULL fixture expands the same fixed partial region to88.
        # Expand its declared count to128; retain 22 patches and23 PCM slots.
        struct.pack_into('<H',data,0x10c,128)
        for partial in range(128):
            # +0x10 is the sample reference, not a unique partial identifier.
            # Every timing case deliberately uses sample0.
            struct.pack_into('<H',data,0x10e00+128*partial+0x10,0)
        # Scale existing integer PCM rather than regenerating noise with a new
        # amplitude: randint changes its random sequence when bounds change.
        for sample in range(23):
            pos = 0x2ac00 + sample*0x2400
            pcm = struct.unpack_from('<4608h',data,pos)
            scaled = [v*args.pcm_gain for v in pcm]
            assert all(-32768 <= v <= 32767 for v in scaled)
            struct.pack_into('<4608h',data,pos,*scaled)
        manifest['pcm_sha256'] = [hashlib.sha256(data[0x2ac00+i*0x2400:0x2ac00+(i+1)*0x2400]).hexdigest() for i in range(23)]
        manifest['encoded_pcm_multiplier'] = args.pcm_gain
        manifest['source_gain_db'] = 20*math.log10(args.pcm_gain)
        manifest['revision'] = 'V2 loud' if args.pcm_gain != 1 else 'V1'
        image.write_bytes(data)
        manifest['sha256']=hashlib.sha256(data).hexdigest()
        manifest['declared_partial_count']=128
        manifest['sample_reference_override']='All partials use sample0 at +0x10'
        image.with_suffix('.IMG.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        assert len(data) == 737280
        for program, patch in enumerate(spec['patches']):
            mapping = patch.get('key_map', [patch.get('partial',0)]*88)
            base = 0x8e00 + 256*program
            assert list(data[base+0x20:base+0x78]) == mapping
            for note, partial in zip(range(21, 109), mapping):
                rate = rates[partial]
                pos = 0x10e00 + 128*partial
                assert data[pos+0x52:pos+0x56] == bytes([64,96,64,96])
                assert data[pos+0x56:pos+0x5a] == bytes([rate]*4)
                rows.append(dict(disk=image.name, program_change=program,
                    display_program=program+1, patch=patch['name'], midi_note=note,
                    partial=partial, time_1=rate, time_2=rate, time_3=rate,
                    time_4=rate, image_sha256=manifest['sha256']))
        print(image.name, manifest['sha256'], flush=True)
    assert hashlib.sha256(template.read_bytes()).hexdigest() == before
    assert {r['time_1'] for r in rows} == set(range(128))
    with (out/'capture-map.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out/'capture-map.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')
    capture_intro = (
        'GAIN PILOT ONLY: patch01 SURVEY, MIDI73, velocity127, one layer.\n'
        'Capture3 seconds held and3 seconds release to check the louder level.\n'
        'Do not repeat the existing survey just because this revision is louder.\n'
        if args.pcm_gain != 1 else
        'FIRST PASS ONLY: patch01 SURVEY. Capture MIDI23..107, step4.\n'
        'Exactly22 notes,3 seconds held and3 seconds release, velocity127.\n'
    )
    (out/'README.txt').write_text(
        'RoboSampler TVF envelope timing kit\n\n'
        f'Image: {args.image_name}; source PCM gain {args.pcm_gain}x ({20*math.log10(args.pcm_gain):.2f}dB).\n'
        + capture_intro +
        'Every four adjacent keys select one Time setting; all88 keys remain mapped.\n'
        'Use MIDI channel 1, sustain off, mod wheel zero, centered pitch bend.\n'
        'Send CC7=127 and CC10=64 before capture. RoboSampler programs1..22\n'
        'are raw MIDI0..21; native Perform display labels101..122 are separate.\n'
        'No30+30-second requirement and no full88-note/all22-patch capture.\n'
        'Disable normalization/effects/automatic looping; preserve note-on and\n'
        'note-off timing. Keep the release available within your chosen window.\n'
        'Incomplete transitions are useful bounds; assess the survey first, then\n'
        'request only specific additional notes or longer takes if needed.\n'
        'Keep output/interface gain fixed and leave recording headroom.\n\n'
        'Return RoboSampler ZIP containing original WAVs, SFZ, metadata.json\n'
        'and metadata.txt, in the same format as your existing survey ZIP.\n'
        'Numeric MIDI values in metadata.json are authoritative.\n'
        'Use raw WAVs for analysis, not SFZ gain/release processing.\n'
        'Keep recording/interface gain fixed within a capture session.\n\n'
        'Patches02..07 cover all128 Time values: 000-021,022-043,044-065,\n'
        '066-087,088-109,110-127. Four adjacent keys per value; patch07 repeats\n'
        '127 on spare keys. Patches08..22 hold selected individual rates across\n'
        'all88 keys to separate keyboard dependence from rate changes.\n\n'
        'Those additional patches are optional follow-up tools, not a request\n'
        'to record everything. Only capture the notes requested for that stage.\n\n'
        'Levels64/96/64/96 and equal Times exercise rising/falling held stages\n'
        'and note-off. Resonance0 and LFO depths0 isolate envelope timing.\n'
        'Compare stage durations and normalized trajectories before refitting\n'
        'filter response. Incomplete stages are censored measurements, not fails.\n'
        'This set tests TVF envelopes, not LFO or TVA speed.\n\n'
        '720KB sample images: load directly via Gotek, no system-disk repacker.\n'
        'Byte maps/geometry verified; new fixtures have not yet been auditioned\n'
        'on native firmware or hardware. First audition low/mid/high keys.\n'
        'Local template content: keep generated disks out of source distributions.\n',
        encoding='utf-8')
    (out/'build-validation.json').write_text(json.dumps(dict(
        passed=True, disks=len(banks), patch_note_rows=len(rows),
        time_values=128, mapped_keys=[21,108], template_sha256=before,
        verification='Image geometry, all patch key maps and envelope bytes; template immutable',
        limits='No native audition or hardware measurement yet'), indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
