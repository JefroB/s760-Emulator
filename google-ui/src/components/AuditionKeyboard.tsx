import React, { useState } from 'react';
import { DiskImage } from '../types/sampler';
import { soundFx } from '../audio/soundFx';

interface AuditionKeyboardProps {
  powerOn: boolean;
  mountedDisk: DiskImage | null;
  selectedDisk: DiskImage;
  currentPatchName: string;
  volume: number;
  onEventEmit: (type: string, payload: any) => void;
}

export const AuditionKeyboard: React.FC<AuditionKeyboardProps> = ({
  powerOn,
  mountedDisk,
  selectedDisk,
  currentPatchName,
  volume,
  onEventEmit,
}) => {
  const [activeKey, setActiveKey] = useState<number | null>(null);

  const activeDisk = mountedDisk || selectedDisk;

  // 17-key mini chromatic keyboard (C3 to E4)
  const keys = [
    { note: 48, name: 'C3', isBlack: false },
    { note: 49, name: 'C#3', isBlack: true },
    { note: 50, name: 'D3', isBlack: false },
    { note: 51, name: 'D#3', isBlack: true },
    { note: 52, name: 'E3', isBlack: false },
    { note: 53, name: 'F3', isBlack: false },
    { note: 54, name: 'F#3', isBlack: true },
    { note: 55, name: 'G3', isBlack: false },
    { note: 56, name: 'G#3', isBlack: true },
    { note: 57, name: 'A3', isBlack: false },
    { note: 58, name: 'A#3', isBlack: true },
    { note: 59, name: 'B3', isBlack: false },
    { note: 60, name: 'C4', isBlack: false },
    { note: 61, name: 'C#4', isBlack: true },
    { note: 62, name: 'D4', isBlack: false },
    { note: 63, name: 'D#4', isBlack: true },
    { note: 64, name: 'E4', isBlack: false },
  ];

  const handleTriggerNote = (note: number, noteName: string) => {
    if (!powerOn) return;
    setActiveKey(note);
    soundFx.auditionSample(currentPatchName, note);
    onEventEmit('NOTE_ON', {
      note,
      noteName,
      patch: currentPatchName,
      velocity: 100,
      vol: volume,
    });

    setTimeout(() => {
      setActiveKey((curr) => (curr === note ? null : curr));
    }, 280);
  };

  return (
    <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-3 bg-neutral-900/90 rounded-md border border-neutral-800 shadow-md">
      {/* Current Sample Info */}
      <div className="flex flex-col gap-1 min-w-[240px]">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-400">
            AUDITION OUTPUT
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        </div>
        <div className="text-xs font-mono font-bold text-neutral-100 truncate">
          {currentPatchName}
        </div>
        <div className="text-[11px] font-mono text-neutral-400">
          Source: <span className="text-neutral-300">{activeDisk.label}</span> ·{' '}
          <span className="text-neutral-400">{activeDisk.sampleRate}</span>
        </div>
      </div>

      {/* Mini Keyboard Bed */}
      <div className="relative flex items-end h-16 bg-neutral-950 p-1 rounded border border-neutral-800 shadow-inner">
        {keys.map((k) => {
          const isPressed = activeKey === k.note;
          if (k.isBlack) {
            return (
              <button
                key={k.note}
                type="button"
                onClick={() => handleTriggerNote(k.note, k.name)}
                disabled={!powerOn}
                title={`Key ${k.name}`}
                className={`relative z-10 -mx-2.5 w-5 h-10 rounded-b-[2px] transition-all cursor-pointer ${
                  isPressed
                    ? 'bg-amber-500 shadow-[0_0_8px_#f59e0b]'
                    : 'bg-neutral-800 hover:bg-neutral-700 active:bg-amber-600'
                } border border-black shadow-sm disabled:opacity-40 disabled:cursor-not-allowed`}
              />
            );
          }
          return (
            <button
              key={k.note}
              type="button"
              onClick={() => handleTriggerNote(k.note, k.name)}
              disabled={!powerOn}
              title={`Key ${k.name}`}
              className={`w-7 h-14 rounded-b-[3px] border border-neutral-700 transition-all cursor-pointer flex flex-col justify-end items-center pb-1 ${
                isPressed
                  ? 'bg-amber-200 shadow-[0_0_8px_#fde68a]'
                  : 'bg-neutral-200 hover:bg-neutral-100 active:bg-amber-100'
              } text-[8px] font-mono font-bold text-neutral-700 disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              {k.name === 'C3' || k.name === 'C4' ? k.name : ''}
            </button>
          );
        })}
      </div>

      {/* Quick Audition Pads */}
      <div className="flex items-center gap-1.5">
        {['ROOT C', 'FIFTH G', 'OCT C', 'ROLL'].map((pad, i) => (
          <button
            key={pad}
            type="button"
            onClick={() => handleTriggerNote(48 + i * 4, pad)}
            disabled={!powerOn}
            className="px-2.5 py-1.5 rounded text-[10px] font-mono font-bold uppercase tracking-wide bg-neutral-800 hover:bg-neutral-750 active:bg-amber-600/30 text-neutral-300 border border-neutral-700 transition-colors disabled:opacity-40"
          >
            {pad}
          </button>
        ))}
      </div>
    </div>
  );
};
