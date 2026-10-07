/**
 * Types & Data structures for the Roland S-760 Sampler digital twin
 * with FlashFloppy Gotek USB modification.
 */

export interface DiskImage {
  id: string;
  slot: string; // e.g. "001/084"
  filename: string;
  folder: string;
  label: string;
  sizeKb: number;
  format: 'IMG' | 'DSK' | 'HFE';
  patches: string[];
  sampleWaveformType: 'strings' | 'brass' | 'synth' | 'drum' | 'piano' | 'bass';
  sampleRate: '48.0kHz' | '44.1kHz' | '32.0kHz' | '22.05kHz';
  samplePoints: {
    start: number;
    loopStart: number;
    loopEnd: number;
    totalSamples: number;
  };
}

export type SamplerMode = 'PERF' | 'PATCH' | 'PART' | 'SAMPLE' | 'SYSTEM' | 'DISK';

export interface SamplerState {
  powerOn: boolean;
  volume: number; // 0 - 100
  volumeAngle: number; // -135 to +135 deg
  alphaDialAngle: number; // continuous deg
  mode: SamplerMode;
  subMode: string;
  activeCursorField: number;
  cursorRow: number;
  cursorCol: number;
  backlightColor: 'emerald' | 'amber';
  
  // Patch & Sample Selection
  currentPatchIndex: number;
  currentPerfIndex: number;
  sampleZoom: number; // 1, 4, 16
  sampleScrub: number; // 0 to 100

  // Gotek state
  gotek: {
    selectedImageIndex: number;
    mountedImageIndex: number | null;
    isBusy: boolean;
    currentTrack: number;
    currentSide: number;
    usbInserted: boolean;
    dialAngle: number;
    statusText: string;
  };

  // Activity & Peak indicators
  peakL: boolean;
  peakR: boolean;
  midiRx: boolean;
}

export interface HardwareEvent {
  id: string;
  timestamp: string;
  source: 'FRONT_PANEL' | 'GOTEK' | 'SYSTEM' | 'MIDI';
  type: string;
  payload: Record<string, any>;
}

export const DEFAULT_DISK_IMAGES: DiskImage[] = [
  {
    id: 'd1',
    slot: '001/084',
    filename: 'S760_SYS224.IMG',
    folder: '/ROLAND/',
    label: 'Roland System Software v2.24',
    sizeKb: 1440,
    format: 'IMG',
    patches: ['SYS: OS v2.24 Boot', 'SYS: SCSI Driver 7.1', 'SYS: Memory Test', 'SYS: Mouse Driver'],
    sampleWaveformType: 'synth',
    sampleRate: '48.0kHz',
    samplePoints: { start: 0, loopStart: 2400, loopEnd: 48000, totalSamples: 48000 }
  },
  {
    id: 'd2',
    slot: '002/084',
    filename: 'LCD701_STRINGS.IMG',
    folder: '/ROLAND/',
    label: 'L-CD701 Orchestral Strings',
    sizeKb: 1440,
    format: 'IMG',
    patches: ['01 Warm String Ens', '02 Marcato Violins', '03 Celli Legato', '04 Pizzicato Sec'],
    sampleWaveformType: 'strings',
    sampleRate: '44.1kHz',
    samplePoints: { start: 120, loopStart: 18400, loopEnd: 42000, totalSamples: 44100 }
  },
  {
    id: 'd3',
    slot: '003/084',
    filename: 'LCD702_BRASS.IMG',
    folder: '/ROLAND/',
    label: 'L-CD702 Brass & Woodwinds',
    sizeKb: 1440,
    format: 'IMG',
    patches: ['01 Tight French Horn', '02 Big Band Trumpet', '03 Trombone Section', '04 Alto Sax Solo'],
    sampleWaveformType: 'brass',
    sampleRate: '44.1kHz',
    samplePoints: { start: 80, loopStart: 15200, loopEnd: 39500, totalSamples: 44100 }
  },
  {
    id: 'd4',
    slot: '004/084',
    filename: 'LCD703_ETHNIC.IMG',
    folder: '/ROLAND/',
    label: 'L-CD703 World Instruments',
    sizeKb: 1440,
    format: 'IMG',
    patches: ['01 Shakuhachi Air', '02 Koto Pluck', '03 African Djembe', '04 Celtic Whistle'],
    sampleWaveformType: 'synth',
    sampleRate: '32.0kHz',
    samplePoints: { start: 200, loopStart: 11000, loopEnd: 31000, totalSamples: 32000 }
  },
  {
    id: 'd5',
    slot: '005/084',
    filename: 'VINTAGE_SYNTHS.IMG',
    folder: '/ROLAND/',
    label: 'Roland Jupiter & Juno Bank',
    sizeKb: 1440,
    format: 'IMG',
    patches: ['01 JP-8 Poly Brass', '02 Juno-106 Sub Bass', '03 D-50 Digital Native', '04 SH-101 Acid Lead'],
    sampleWaveformType: 'synth',
    sampleRate: '48.0kHz',
    samplePoints: { start: 50, loopStart: 8500, loopEnd: 46000, totalSamples: 48000 }
  },
  {
    id: 'd6',
    slot: '006/084',
    filename: 'DANCE_909_KIT.IMG',
    folder: '/ROLAND/',
    label: 'TR-909 & 808 Studio Rhythm',
    sizeKb: 1440,
    format: 'IMG',
    patches: ['01 TR-909 Tight Kit', '02 TR-808 Boomy Kit', '03 909 Open Hat/Clap', '04 CR-78 Retro Beat'],
    sampleWaveformType: 'drum',
    sampleRate: '44.1kHz',
    samplePoints: { start: 0, loopStart: 28000, loopEnd: 44100, totalSamples: 44100 }
  },
  {
    id: 'd7',
    slot: '007/084',
    filename: 'ACOUSTIC_PIANO.IMG',
    folder: '/ROLAND/',
    label: 'Concert Grand Piano 16MB',
    sizeKb: 1440,
    format: 'IMG',
    patches: ['01 S-760 Grand 16MB', '02 Bright Rock Piano', '03 Honky Tonk Saloon', '04 Rhodes EP Warm'],
    sampleWaveformType: 'piano',
    sampleRate: '48.0kHz',
    samplePoints: { start: 30, loopStart: 21000, loopEnd: 47500, totalSamples: 48000 }
  },
  {
    id: 'd8',
    slot: '008/084',
    filename: 'FRETLESS_BASS.IMG',
    folder: '/ROLAND/',
    label: 'Jaco Fretless & Slap Bass',
    sizeKb: 1440,
    format: 'IMG',
    patches: ['01 Jaco Warm Fretless', '02 Marcus Funk Slap', '03 P-Bass Finger Pick', '04 Upright Acoustic'],
    sampleWaveformType: 'bass',
    sampleRate: '44.1kHz',
    samplePoints: { start: 60, loopStart: 14000, loopEnd: 38000, totalSamples: 44100 }
  }
];
