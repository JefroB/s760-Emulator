from pathlib import Path
import json,sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from s760_runtime import NativeRuntime,RuntimeConfig

def runtime(tmp_path,monkeypatch,result=None,data=bytes(range(256))*2):
    machine=NativeRuntime(RuntimeConfig(None,None,None,tmp_path))
    def request(op,**kw):
        if kw.get('down'):
            (tmp_path/'scsi-hd0-export.img').write_bytes(data)
            (tmp_path/'scsi-hd0-export.img.status').write_text(json.dumps(result or {'ok':True,'bytes':len(data),'error':''}))
        return ({'ok':True},[])
    monkeypatch.setattr(machine,'request',request)
    return machine

def test_scsi_export_is_exact_and_refuses_existing_destination(tmp_path,monkeypatch):
    machine=runtime(tmp_path,monkeypatch);dest=tmp_path/'saved.img'
    machine.export_scsi_hd0(dest)
    assert dest.read_bytes()==bytes(range(256))*2
    monkeypatch.setattr(machine,'request',lambda *a,**kw:pytest.fail('Existing destination reached native export'))
    with pytest.raises(FileExistsError):machine.export_scsi_hd0(dest)
    assert dest.read_bytes()==bytes(range(256))*2

@pytest.mark.parametrize('result',[{'ok':False,'error':'SCSI controller is busy'},{'ok':True,'bytes':1024,'error':''}])
def test_failed_scsi_export_does_not_publish(tmp_path,monkeypatch,result):
    machine=runtime(tmp_path,monkeypatch,result);dest=tmp_path/'saved.img'
    with pytest.raises((RuntimeError,ValueError)):machine.export_scsi_hd0(dest)
    assert not dest.exists()
    assert not list(tmp_path.glob('*.pending'))
