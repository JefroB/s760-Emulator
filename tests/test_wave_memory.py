import pytest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from s760_runtime import RuntimeConfig, NativeRuntime

@pytest.mark.parametrize('size',[8,16,32])
def test_supported_wave_memory(size):
    cfg=RuntimeConfig(None,None,None,None,wave_memory_mb=size)
    cfg.audio_arguments()

@pytest.mark.parametrize('size',[2,0,64,'32',True,None,32.0])
def test_invalid_wave_memory(size):
    with pytest.raises(ValueError,match='memory'):
        RuntimeConfig(None,None,None,None,wave_memory_mb=size).audio_arguments()

def test_wave_memory_default_and_checkpoint_identity(tmp_path,monkeypatch):
    import s760_runtime
    for name in ('mame','boot','system'):(tmp_path/name).write_bytes(name.encode())
    (tmp_path/'scripts').mkdir();(tmp_path/'scripts/s760_runtime.lua').write_bytes(b'protocol')
    monkeypatch.setattr(s760_runtime,'application_root',lambda:tmp_path)
    cfg=RuntimeConfig(tmp_path/'mame',tmp_path/'boot',tmp_path/'system',tmp_path)
    assert cfg.wave_memory_mb==32
    runtime=NativeRuntime(cfg);large=runtime._checkpoint_identity()
    cfg.wave_memory_mb=8;small=runtime._checkpoint_identity()
    assert large['wave_memory_mb']==32 and small['wave_memory_mb']==8
    assert large!=small
