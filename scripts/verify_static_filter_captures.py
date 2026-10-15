"""Static BP/HP capture validation retaining recording-band DAC images.

Fixed recurrence428/85; gain/affine phase learned on1..2.4s only, withheld3..4.5s.
Numerical comparison of existing physical captures, not moving-filter qualification.
"""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import optimize,signal
ROOT=Path(__file__).resolve().parents[1]
PERIOD=4458.136121698991 # Recording samples/4096-source-sample period; prior bypass calibration.
FS=48000
SOURCE_RATE=4096*FS/PERIOD
CAPTURES={'s760_01 REF NOISE_20261010_121558.zip': 'f4aa569c7c5148f5e49004f6ddef1591b51143bd5a4b38c09f839fd1d1856d44', 's760_01 BP C64 R64_20261010_162825.zip': '178008864049418d53e632d1523391078ef68dabed4496f5db0110f84d37732d', 's760_02 HP C64 R64_20261010_162854.zip': '65e80dccf01f6e4f20e77bbcc3ee20a368e781aa1548a6085c812e45ab29bd4e'}

def periodic_shift(wave,source_samples):
    # The FFT period may exceed4096 points. Phase uses physical source samples,
    # including image harmonics above the source Nyquist, not FFT-array indices.
    k=np.arange(len(wave)//2+1)
    return np.fft.irfft(np.fft.rfft(wave)*np.exp(-2j*np.pi*k*source_samples/4096),n=len(wave))

def folded(wave,start,end,points,oversample):
    starts=np.arange(start*FS,end*FS-PERIOD,PERIOD)
    value=np.mean([np.interp((a+np.arange(points)*PERIOD/points)*oversample,np.arange(len(wave)),wave) for a in starts],axis=0)
    return value-value.mean()

def validate_capture(waves,points=8192,oversample=8,cutoff=428):
    if points<4096 or points%4096 or oversample<1:raise ValueError('Invalid analysis resolution')
    waves=[signal.resample_poly(y,oversample,1,window=('kaiser',10.)) for y in waves] if oversample>1 else waves
    base=folded(waves[0],1,5,points,oversample);spectrum=np.fft.rfft(base);k=np.arange(len(spectrum))
    spectrum[k*SOURCE_RATE/4096>FS/2]=0 # No evidence outside the recording bandwidth.
    z=np.exp(-2j*np.pi*k/4096);c=cutoff/16384;d=85/4096
    denominator=1-(2-c*d-c*c)*z+(1-c*d)*z*z;rows=[]
    for mode in (1,2):
        numerator=c*(1-z) if mode==1 else (1-z)**2
        prediction=np.fft.irfft(spectrum*numerator/denominator,n=points);training=[]
        for start in (1.,1.3,1.6,1.9):
            value=folded(waves[mode],start,start+.5,points,oversample)
            cross=np.fft.irfft(np.fft.rfft(value)*np.conj(np.fft.rfft(prediction)),n=points)
            lag=int(np.argmax(cross))*4096/points
            def error(delay):
                p=periodic_shift(prediction,delay);gain=np.dot(value,p)/np.dot(p,p)
                return np.mean((value-gain*p)**2)
            fit=optimize.minimize_scalar(error,bounds=(lag-3,lag+3),method='bounded')
            training.append(dict(start=start,end=start+.5,center=start+.25,phase=(fit.x+start*SOURCE_RATE)%4096))
        phase=np.unwrap(np.array([v['phase'] for v in training])*2*np.pi/4096)*4096/(2*np.pi)
        slope,intercept=np.polyfit([v['center'] for v in training],phase,1)
        early=folded(waves[mode],1,2.5,points,oversample)
        p=periodic_shift(prediction,intercept+slope*1.75-SOURCE_RATE);gain=float(np.dot(early,p)/np.dot(p,p))
        withheld=folded(waves[mode],3,4.5,points,oversample)
        forecast=gain*periodic_shift(prediction,intercept+slope*3.75-3*SOURCE_RATE)
        relative=float(np.linalg.norm(withheld-forecast)/np.linalg.norm(withheld))
        rows.append(dict(mode='BP' if mode==1 else 'HP',cutoff=cutoff,damping=85,training=training,gain=gain,phase_slope=float(slope),heldout_correlation=float(np.corrcoef(withheld,forecast)[0,1]),heldout_rms_error_percent=100*relative))
    return dict(points=points,recording_oversample=oversample,rows=rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--state-dir',type=Path,required=True);ap.add_argument('--capture-dir',type=Path,default=ROOT/'test-recordings');a=ap.parse_args();out=a.state_dir.resolve()
    if out.exists() and any(out.iterdir()):ap.error('Use a fresh private output directory')
    out.mkdir(parents=True,exist_ok=True);waves=[];audits=[]
    for name,expected in CAPTURES.items():
        raw=(a.capture_dir/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected,'Capture identity mismatch'
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            meta=json.loads(archive.read('metadata.json'));wav=archive.read(meta['samples'][0]['filename']);values,rate=sf.read(io.BytesIO(wav),always_2d=True)
        assert rate==FS and len(values)>4.5*FS and np.isfinite(values).all() and np.max(np.abs(values))<1
        waves.append(values[:,0]);audits.append(dict(file=name,zip_sha256=expected,wav_sha256=hashlib.sha256(wav).hexdigest(),frames=len(values),sample_rate=rate))
    before=validate_capture(waves,4096,8)
    corrected=validate_capture(waves,8192,8)
    sensitivity=validate_capture(waves,16384,16)
    negative=validate_capture(waves,8192,8,430)
    assert before['rows'][1]['heldout_rms_error_percent']>1,'Expected old folding defect did not reproduce'
    for run in (corrected,sensitivity):assert all(row['heldout_rms_error_percent']<1 for row in run['rows']),'Static waveform target failed'
    assert negative['rows'][1]['heldout_rms_error_percent']>1,'Wrong coefficient was not discriminated'
    result=dict(passed=True,captures=audits,calibrated_recording_period=PERIOD,source_rate=SOURCE_RATE,old_analysis=before,corrected=corrected,resolution_check=sensitivity,wrong_cutoff_control=negative,limits='One stationary C64/R64 BP/HP capture pair with calibrated bypass; fitted gain/training-only phase, not raw whole-chip identity. No renderer changes, moving/resonant accuracy, arbitrary coefficients, clocks or MIDI arbitration claim.')
    (out/'static-filter-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['captures']},indent=2))
if __name__=='__main__':main()
