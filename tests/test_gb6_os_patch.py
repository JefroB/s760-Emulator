"""Safety, instruction/peripheral model and optional local-firmware reproduction."""
import hashlib
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from patch_gb6_os import (DISCONNECT_OFFSET, IMAGE_SIZE, OUTPUT_SHA256,
                          PATCH_END, PATCH_START, SOURCE_SHA256, decoder, patch_image)


def test_source_safety(tmp_path):
    source, output = tmp_path/'original.IMG', tmp_path/'patched.IMG'
    original = bytes(IMAGE_SIZE)
    source.write_bytes(original)
    with pytest.raises(ValueError, match='unmodified'):
        patch_image(source, output)
    assert not output.exists()
    with pytest.raises(ValueError, match='differ'):
        patch_image(source, source)
    with pytest.raises(ValueError, match='.IMG output'):
        patch_image(source, tmp_path/'firmware.txt')
    assert source.read_bytes() == original


@pytest.mark.parametrize('profile', ('v8', 'v9'))
def test_decoded_peripheral_matrix(profile):
    pypcode = pytest.importorskip('pypcode')
    code = decoder(profile)
    insns = pypcode.Context('MCS96:LE:16:default').disassemble(code, base_address=0x43B5).instructions
    decoded = {i.addr.offset-0x43B5:i for i in insns}
    assert sum(i.length for i in insns) == 92

    def run(x, y, buttons, initial):
        r, selected, counts, events, pc, equal = {0:0}, initial, {'x':x,'y':y}, [], 0, False
        while pc < 92:
            i = decoded[pc]
            b = code[pc:pc+i.length]
            pc += i.length
            if i.mnem == 'SCALL':
                assert any(t in i.body.lower() for t in ('0x4476','0x446f'))
            elif b[0] == 0xB1: r[b[2]] = b[1]
            elif b[:4] == bytes.fromhex('C7 01 08 F0'):
                new = int(bool(r[b[4]] & 0x40))
                if new != selected:
                    axis = 'x' if new else 'y'
                    counts[axis] = 0
                    events.append(('reset',axis))
                selected = new
            elif b[:4] == bytes.fromhex('B3 01 08 F0'):
                axis = 'y' if selected else 'x'
                events.append(('read',axis))
                r[b[4]] = (counts[axis]+8) | buttons
            elif b[0] == 0x71: r[b[2]] &= b[1]
            elif b[0] == 0x79: r[b[2]] = (r[b[2]]-b[1]) & 255
            elif b[0] == 0xB0: r[b[2]] = r[b[1]]
            elif b[0] == 0x19: r[b[2]] = (r[b[2]] << b[1]) & 255
            elif b[0] == 0x99: equal = r[b[2]] == b[1]
            elif b[0] == 0xD7:
                if not equal: pc += int.from_bytes(b[1:2], signed=True)
            else: assert i.mnem == 'NOP'
        return r, events, selected, counts

    for x in range(-8,8):
        for y in range(-8,8):
            for buttons in (0,0x10,0x20,0x30):
                for initial in (0,1):
                    r, events, selected, counts = run(x,y,buttons,initial)
                    assert r[0xAD] == max(-63,x*(8 if profile=='v8' else 4)) & 255
                    assert r[0xD3] == (max(-63,y*4) & 255 if not initial else 0)
                    expected = [('read','x'),('reset','x'),('read','y'),('reset','y')]
                    assert events == ([('reset','y')]+expected if initial else expected)
                    assert selected == 0 and counts == {'x':0,'y':0}


@pytest.mark.parametrize('profile', ('v8','v9'))
def test_optional_image_reproduction(tmp_path, profile):
    source = ROOT/'roms/System/S760224.IMG'
    if not source.is_file():
        pytest.skip('User-supplied original OS2.24 not provisioned')
    original = source.read_bytes()
    assert hashlib.sha256(original).hexdigest() == SOURCE_SHA256
    output = tmp_path/f'GB6-{profile}.IMG'
    assert patch_image(source,output,profile)['output_sha256'] == OUTPUT_SHA256[profile]
    image = output.read_bytes()
    assert image[:PATCH_START] == original[:PATCH_START]
    assert image[PATCH_END:DISCONNECT_OFFSET] == original[PATCH_END:DISCONNECT_OFFSET]
    assert image[DISCONNECT_OFFSET+1:] == original[DISCONNECT_OFFSET+1:]
    with pytest.raises(FileExistsError): patch_image(source,output,profile)
    assert source.read_bytes() == original and output.read_bytes() == image
