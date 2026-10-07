import React, { useState, useRef } from 'react';
import { SamplerState, SamplerMode, DiskImage } from '../types/sampler';
import { RolandLCD } from './RolandLCD';
import { GotekBay } from './GotekBay';
import { RackEar } from './RackEars';
import { soundFx } from '../audio/soundFx';

interface S760FrontPanelProps {
  state: SamplerState;
  diskList: DiskImage[];
  onTogglePower: () => void;
  onSetVolume: (vol: number) => void;
  onSetMode: (mode: SamplerMode) => void;
  onAlphaDialStep: (delta: number) => void;
  onNavigate: (dir: 'UP' | 'DOWN' | 'LEFT' | 'RIGHT') => void;
  onIncDec: (delta: number) => void;
  onEnter: () => void;
  onExit: () => void;
  onSoftKey: (index: number) => void;
  onSelectDiskIndex: (idx: number) => void;
  onMountDisk: () => void;
  onToggleUsb: () => void;
  onEventEmit: (type: string, payload: any) => void;
  onTriggerAudition: () => void;
}

export const S760FrontPanel: React.FC<S760FrontPanelProps> = ({
  state,
  diskList,
  onTogglePower,
  onSetVolume,
  onSetMode,
  onAlphaDialStep,
  onNavigate,
  onIncDec,
  onEnter,
  onExit,
  onSoftKey,
  onSelectDiskIndex,
  onMountDisk,
  onToggleUsb,
  onEventEmit,
  onTriggerAudition,
}) => {
  const [pressedBtn, setPressedBtn] = useState<string | null>(null);

  // Drag handling for Master Volume
  const volDragStart = useRef<number | null>(null);
  const initialVol = useRef<number>(state.volume);

  // Drag handling for Alpha Dial
  const alphaDragStart = useRef<number | null>(null);
  const lastStepAngle = useRef<number>(0);

  const triggerButton = (id: string, action: () => void, soundType: 'button' | 'rubber' = 'rubber') => {
    setPressedBtn(id);
    soundFx.playClick(soundType);
    action();
    setTimeout(() => {
      setPressedBtn((curr) => (curr === id ? null : curr));
    }, 140);
  };

  // Master Volume Drag
  const handleVolumeMouseDown = (e: React.MouseEvent) => {
    volDragStart.current = e.clientY;
    initialVol.current = state.volume;
    soundFx.playClick('dial');

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (volDragStart.current === null) return;
      const dy = volDragStart.current - moveEvent.clientY;
      const newVol = Math.max(0, Math.min(100, initialVol.current + Math.round(dy * 0.8)));
      onSetVolume(newVol);
    };

    const handleMouseUp = () => {
      volDragStart.current = null;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const handleVolumeWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 3 : -3;
    const newVol = Math.max(0, Math.min(100, state.volume + delta));
    soundFx.playClick('dial');
    onSetVolume(newVol);
  };

  // Alpha Dial Drag
  const handleAlphaMouseDown = (e: React.MouseEvent) => {
    alphaDragStart.current = e.clientY;
    lastStepAngle.current = 0;
    soundFx.playClick('dial');

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (alphaDragStart.current === null) return;
      const dy = alphaDragStart.current - moveEvent.clientY;
      const steps = Math.trunc(dy / 10);
      if (steps !== 0) {
        onAlphaDialStep(steps > 0 ? 1 : -1);
        alphaDragStart.current = moveEvent.clientY;
        soundFx.playClick('dial');
      }
    };

    const handleMouseUp = () => {
      alphaDragStart.current = null;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const handleAlphaWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 1 : -1;
    soundFx.playClick('dial');
    onAlphaDialStep(delta);
  };

  const selectedDisk = diskList[state.gotek.selectedImageIndex] || diskList[0];
  const mountedDisk =
    state.gotek.mountedImageIndex !== null ? diskList[state.gotek.mountedImageIndex] : null;

  // Active patch name
  const currentPatchName =
    mountedDisk && mountedDisk.patches[state.currentPatchIndex % mountedDisk.patches.length]
      ? mountedDisk.patches[state.currentPatchIndex % mountedDisk.patches.length]
      : selectedDisk.patches[0];

  return (
    <div className="relative w-full overflow-x-auto py-4 flex justify-center items-center">
      {/* 19-inch 1U Main Chassis Container */}
      <div
        className="relative flex items-stretch rounded-[2px] bg-brushed-metal-horizontal shadow-[0_20px_50px_rgba(0,0,0,0.9),0_2px_4px_rgba(255,255,255,0.06)] border-t border-neutral-600/60 border-b border-neutral-850 select-none"
        style={{
          width: '1440px',
          height: '144px',
          minWidth: '1440px',
        }}
      >
        {/* Top Metallic Bevel Highlight */}
        <div className="absolute top-0 inset-x-0 h-[1.5px] bg-gradient-to-r from-neutral-500 via-neutral-300 to-neutral-500 opacity-70 pointer-events-none" />

        {/* Bottom Metallic Shadow Seam */}
        <div className="absolute bottom-0 inset-x-0 h-[2px] bg-gradient-to-r from-neutral-900 via-black to-neutral-900 pointer-events-none" />

        {/* LEFT RACK EAR */}
        <RackEar side="left" />

        {/* ================= SECTION A: LEFT FLANK ================= */}
        <div className="flex items-center px-4 gap-4 border-r border-neutral-700/60">
          {/* Power Rocker Switch */}
          <div className="flex flex-col items-center gap-1">
            <span className="text-[7px] font-mono text-neutral-400 font-bold uppercase tracking-widest">
              POWER
            </span>
            <div
              onClick={() => {
                soundFx.playClick('power');
                onTogglePower();
                onEventEmit('POWER_SWITCH', { powerOn: !state.powerOn });
              }}
              title="Power Rocker Switch [I / O]"
              className="relative w-7 h-12 rounded-[2px] bg-gradient-to-b from-neutral-900 to-black p-1 border border-neutral-700/90 shadow-[inset_0_2px_4px_rgba(0,0,0,0.9)] cursor-pointer group"
            >
              {/* Rocker paddle */}
              <div
                className={`w-full h-full rounded-[1px] transition-all duration-150 flex flex-col justify-between py-1 items-center border ${
                  state.powerOn
                    ? 'bg-gradient-to-b from-[#2a2d33] to-[#1c1e22] border-neutral-600 shadow-[inset_0_2px_2px_rgba(255,255,255,0.2)]'
                    : 'bg-gradient-to-b from-[#181a1e] to-[#282a30] border-neutral-700 shadow-[inset_0_-2px_2px_rgba(255,255,255,0.1)]'
                }`}
              >
                <span
                  className={`text-[8px] font-mono font-bold leading-none ${
                    state.powerOn ? 'text-emerald-400 drop-shadow-[0_0_2px_#34d399]' : 'text-neutral-500'
                  }`}
                >
                  I
                </span>
                <span
                  className={`text-[8px] font-mono font-bold leading-none ${
                    !state.powerOn ? 'text-amber-400' : 'text-neutral-600'
                  }`}
                >
                  O
                </span>
              </div>
            </div>
          </div>

          {/* 1/4" Stereo PHONES Jack */}
          <div className="flex flex-col items-center gap-1">
            <span className="text-[7px] font-mono text-neutral-400 font-bold uppercase tracking-wider">
              PHONES
            </span>
            {/* Hexagonal Chrome Ferrule & Center Jack Hole */}
            <div
              onClick={onTriggerAudition}
              title="1/4' Stereo Phones Jack (Click to Audition Headphone Sound)"
              className="relative w-8 h-8 rounded-full bg-gradient-to-tr from-neutral-400 via-neutral-200 to-neutral-500 border border-neutral-500 shadow-[0_2px_4px_rgba(0,0,0,0.8)] flex items-center justify-center cursor-pointer hover:brightness-110 active:scale-95"
            >
              {/* Hexagonal Nut imprint */}
              <div className="w-6 h-6 rounded-[3px] rotate-45 border border-neutral-400/80 bg-gradient-to-br from-neutral-300 to-neutral-500 flex items-center justify-center shadow-inner">
                {/* Threaded Ferrule Inner Ring */}
                <div className="w-4 h-4 rounded-full bg-gradient-to-b from-neutral-600 to-neutral-800 border border-neutral-400 flex items-center justify-center">
                  {/* Deep Black 1/4" Socket */}
                  <div className="w-2.5 h-2.5 rounded-full bg-black shadow-[inset_0_1px_3px_rgba(0,0,0,1)] border border-neutral-900" />
                </div>
              </div>
            </div>
          </div>

          {/* Hardware Silkscreen Model Block */}
          <div className="flex flex-col justify-center ml-1 pr-2">
            <div className="flex items-baseline gap-1.5">
              <span className="text-[11px] font-black tracking-tight text-neutral-300 uppercase font-sans">
                DIGITAL SAMPLER
              </span>
              <span className="text-xs font-black tracking-wider text-neutral-100 uppercase bg-neutral-850 px-1.5 py-[0.5px] rounded-[1px] border border-neutral-600">
                S-760
              </span>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[6.5px] font-bold tracking-widest text-neutral-400 uppercase">
                QUICK SAMPLING
              </span>
              <span className="text-[6px] text-neutral-500">/</span>
              <span className="text-[6.5px] font-bold tracking-widest text-amber-400/90 uppercase drop-shadow-[0_0_2px_rgba(251,191,36,0.3)]">
                24-BIT INTERNAL PROCESSING
              </span>
            </div>
          </div>

          {/* Roland 160x64 Backlit Graphic LCD Display & Soft Function Keys Below */}
          <div className="flex flex-col items-center">
            <RolandLCD
              powerOn={state.powerOn}
              mode={state.mode}
              backlightColor={state.backlightColor}
              activePatchName={currentPatchName}
              mountedDisk={mountedDisk}
              selectedDisk={selectedDisk}
              isDiskBusy={state.gotek.isBusy}
              diskTrack={state.gotek.currentTrack}
              sampleZoom={state.sampleZoom}
              sampleScrub={state.sampleScrub}
              volume={state.volume}
              activeCursorField={state.activeCursorField}
            />

            {/* Row of 6 Soft Function Buttons directly under LCD: [F1] to [F6] */}
            <div className="flex items-center justify-between w-[240px] mt-1.5 px-0.5">
              {[
                { label: 'F1', sub: 'PLAY' },
                { label: 'F2', sub: 'ZOOM' },
                { label: 'F3', sub: 'LOOP' },
                { label: 'F4', sub: 'MARK' },
                { label: 'F5', sub: 'COMM' },
                { label: 'F6', sub: 'EXIT' },
              ].map((fBtn, idx) => (
                <div key={fBtn.label} className="flex flex-col items-center">
                  <button
                    type="button"
                    onClick={() => {
                      triggerButton(`SOFT_${fBtn.label}`, () => onSoftKey(idx), 'button');
                    }}
                    title={`Function Key [${fBtn.label}]`}
                    className={`w-7 h-4 rounded-[1.5px] text-[7.5px] font-mono font-bold text-neutral-300 bg-gradient-to-b from-neutral-700 via-neutral-800 to-neutral-900 border border-neutral-600 transition-all ${
                      pressedBtn === `SOFT_${fBtn.label}`
                        ? 'tactile-btn-pressed'
                        : 'tactile-btn hover:brightness-110 active:scale-95'
                    }`}
                  >
                    {fBtn.label}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ================= SECTION B: CENTER CONTROL MATRIX ================= */}
        <div className="flex items-center px-4 gap-5 border-r border-neutral-700/60">
          {/* Master Volume Potentiometer */}
          <div className="flex flex-col items-center">
            <span className="text-[7px] font-mono text-neutral-400 font-bold uppercase tracking-wider mb-1">
              VOLUME
            </span>
            <div className="relative flex items-center justify-center">
              {/* Arc of tick marks */}
              <div className="absolute inset-[-6px] pointer-events-none">
                <svg viewBox="0 0 50 50" className="w-full h-full">
                  {[-135, -90, -45, 0, 45, 90, 135].map((angle, i) => {
                    const rad = ((angle - 90) * Math.PI) / 180;
                    const x1 = 25 + Math.cos(rad) * 20;
                    const y1 = 25 + Math.sin(rad) * 20;
                    const x2 = 25 + Math.cos(rad) * 23;
                    const y2 = 25 + Math.sin(rad) * 23;
                    return (
                      <line
                        key={i}
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke="#8b929e"
                        strokeWidth={i === 0 || i === 6 ? '1.5' : '1'}
                      />
                    );
                  })}
                </svg>
              </div>

              {/* Cylindrical Knob */}
              <div
                onWheel={handleVolumeWheel}
                onMouseDown={handleVolumeMouseDown}
                title="Master Volume (Scroll wheel or Drag up/down)"
                className="relative w-9 h-9 rounded-full cursor-grab active:cursor-grabbing border border-neutral-600 shadow-[0_4px_8px_rgba(0,0,0,0.8),inset_0_1px_2px_rgba(255,255,255,0.4)] hover:brightness-110"
                style={{
                  background:
                    'radial-gradient(circle at 35% 35%, #5a5f68 0%, #292b30 65%, #141517 100%)',
                }}
              >
                {/* Pointer Notch Line */}
                <div
                  className="absolute top-1 left-1/2 -translate-x-1/2 w-0.5 h-3.5 bg-neutral-100 rounded-full shadow-[0_0_2px_#ffffff]"
                  style={{
                    transformOrigin: '50% 14px',
                    transform: `translateX(-50%) rotate(${state.volumeAngle}deg)`,
                  }}
                />
              </div>
            </div>
            <div className="flex justify-between w-10 mt-1 text-[6px] font-mono text-neutral-400">
              <span>MIN</span>
              <span>MAX</span>
            </div>
          </div>

          {/* Mode Selection Buttons: [MODE] [PERF] [PATCH] [PART] [SAMPLE] [SYSTEM] [DISK] */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-1.5">
              <span className="text-[6.5px] font-mono text-neutral-400 font-bold uppercase tracking-widest mr-1">
                MODE
              </span>
              {[
                { id: 'PERF', label: 'PERF' },
                { id: 'PATCH', label: 'PATCH' },
                { id: 'PART', label: 'PART' },
                { id: 'SAMPLE', label: 'SAMPLE' },
                { id: 'SYSTEM', label: 'SYSTEM' },
                { id: 'DISK', label: 'DISK' },
              ].map((m) => {
                const isActive = state.mode === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => {
                      triggerButton(`MODE_${m.id}`, () => onSetMode(m.id as SamplerMode), 'rubber');
                      onEventEmit('MODE_SELECT', { mode: m.id });
                    }}
                    title={`Mode Button [${m.label}]`}
                    className={`px-2 py-1 h-5 rounded-[2px] text-[7.5px] font-mono font-bold tracking-tight border transition-all ${
                      isActive
                        ? 'bg-gradient-to-b from-neutral-800 to-neutral-900 border-amber-500/70 text-amber-300 shadow-[inset_0_1px_2px_rgba(0,0,0,0.8),0_0_5px_rgba(245,158,11,0.25)]'
                        : 'bg-gradient-to-b from-neutral-700 via-neutral-750 to-neutral-850 border-neutral-600 text-neutral-200 tactile-rubber-btn hover:brightness-110 active:scale-95'
                    } ${pressedBtn === `MODE_${m.id}` ? 'tactile-btn-pressed' : ''}`}
                  >
                    {m.label}
                  </button>
                );
              })}
            </div>

            {/* Navigation Cross & Value Steppers: [◄] [►] [▲] [▼] [DEC/-] [INC/+] [ENTER] [EXIT] */}
            <div className="flex items-center gap-2">
              {/* Directional Cluster */}
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => triggerButton('NAV_LEFT', () => onNavigate('LEFT'), 'button')}
                  title="Cursor Left [◄]"
                  className={`w-5 h-4.5 rounded-[2px] text-[8px] font-mono text-neutral-200 bg-neutral-800 border border-neutral-600 ${
                    pressedBtn === 'NAV_LEFT' ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110'
                  }`}
                >
                  ◄
                </button>
                <div className="flex flex-col gap-0.5">
                  <button
                    type="button"
                    onClick={() => triggerButton('NAV_UP', () => onNavigate('UP'), 'button')}
                    title="Cursor Up [▲]"
                    className={`w-5 h-4.5 rounded-[2px] text-[8px] font-mono text-neutral-200 bg-neutral-800 border border-neutral-600 ${
                      pressedBtn === 'NAV_UP' ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110'
                    }`}
                  >
                    ▲
                  </button>
                  <button
                    type="button"
                    onClick={() => triggerButton('NAV_DOWN', () => onNavigate('DOWN'), 'button')}
                    title="Cursor Down [▼]"
                    className={`w-5 h-4.5 rounded-[2px] text-[8px] font-mono text-neutral-200 bg-neutral-800 border border-neutral-600 ${
                      pressedBtn === 'NAV_DOWN' ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110'
                    }`}
                  >
                    ▼
                  </button>
                </div>
                <button
                  type="button"
                  onClick={() => triggerButton('NAV_RIGHT', () => onNavigate('RIGHT'), 'button')}
                  title="Cursor Right [►]"
                  className={`w-5 h-4.5 rounded-[2px] text-[8px] font-mono text-neutral-200 bg-neutral-800 border border-neutral-600 ${
                    pressedBtn === 'NAV_RIGHT' ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110'
                  }`}
                >
                  ►
                </button>
              </div>

              {/* Inc / Dec Buttons */}
              <div className="flex items-center gap-1 ml-1">
                <button
                  type="button"
                  onClick={() => triggerButton('DEC_BTN', () => onIncDec(-1), 'rubber')}
                  title="Value Dec [DEC / -]"
                  className={`px-1.5 h-6 rounded-[2px] text-[7.5px] font-mono font-bold text-neutral-200 bg-gradient-to-b from-neutral-700 to-neutral-850 border border-neutral-600 ${
                    pressedBtn === 'DEC_BTN' ? 'tactile-btn-pressed' : 'tactile-rubber-btn hover:brightness-110'
                  }`}
                >
                  DEC / -
                </button>
                <button
                  type="button"
                  onClick={() => triggerButton('INC_BTN', () => onIncDec(1), 'rubber')}
                  title="Value Inc [INC / +]"
                  className={`px-1.5 h-6 rounded-[2px] text-[7.5px] font-mono font-bold text-neutral-200 bg-gradient-to-b from-neutral-700 to-neutral-850 border border-neutral-600 ${
                    pressedBtn === 'INC_BTN' ? 'tactile-btn-pressed' : 'tactile-rubber-btn hover:brightness-110'
                  }`}
                >
                  INC / +
                </button>
              </div>

              {/* Enter / Exit Buttons */}
              <div className="flex items-center gap-1 ml-1">
                <button
                  type="button"
                  onClick={() => triggerButton('ENTER_BTN', onEnter, 'button')}
                  title="Command Execute [ENTER]"
                  className={`px-2 h-6 rounded-[2px] text-[7.5px] font-mono font-bold text-emerald-300 bg-gradient-to-b from-neutral-700 to-neutral-850 border border-emerald-700/60 ${
                    pressedBtn === 'ENTER_BTN' ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110'
                  }`}
                >
                  ENTER
                </button>
                <button
                  type="button"
                  onClick={() => triggerButton('EXIT_BTN', onExit, 'button')}
                  title="Return / Escape [EXIT]"
                  className={`px-2 h-6 rounded-[2px] text-[7.5px] font-mono font-bold text-rose-300 bg-gradient-to-b from-neutral-700 to-neutral-850 border border-rose-700/60 ${
                    pressedBtn === 'EXIT_BTN' ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110'
                  }`}
                >
                  EXIT
                </button>
              </div>
            </div>
          </div>

          {/* Large Knurled Value / Data Alpha-Dial */}
          <div className="flex flex-col items-center">
            <span className="text-[7px] font-mono text-neutral-400 font-bold uppercase tracking-wider mb-1">
              VALUE / DATA
            </span>
            <div
              onWheel={handleAlphaWheel}
              onMouseDown={handleAlphaMouseDown}
              title="Value / Data Alpha-Dial (Drag or Scroll wheel to adjust values smoothly)"
              className="relative w-15 h-15 rounded-full cursor-grab active:cursor-grabbing border border-neutral-600 shadow-[0_5px_10px_rgba(0,0,0,0.85),inset_0_1px_3px_rgba(255,255,255,0.4)] hover:brightness-105"
              style={{
                background:
                  'radial-gradient(circle at 40% 40%, #52565e 0%, #282a2f 65%, #151618 100%)',
              }}
            >
              {/* Concentric knurled perimeter rings */}
              <div
                className="absolute inset-0 rounded-full opacity-70 bg-knurled-rim"
                style={{
                  transform: `rotate(${state.alphaDialAngle}deg)`,
                }}
              />

              {/* Machined Inner Disc */}
              <div className="absolute inset-2 rounded-full bg-gradient-to-tr from-neutral-800 via-neutral-650 to-neutral-500 border border-neutral-600 flex items-center justify-center">
                {/* Finger Dimple / Indentation */}
                <div
                  className="w-3.5 h-3.5 rounded-full bg-gradient-to-br from-neutral-900 to-neutral-700 border border-neutral-500 shadow-inner"
                  style={{
                    transform: `rotate(${state.alphaDialAngle}deg) translateY(-14px)`,
                    transformOrigin: '50% 14px',
                  }}
                />
              </div>
            </div>
            <span className="text-[6.5px] font-mono text-neutral-400 uppercase tracking-tight mt-0.5">
              ALPHA-DIAL
            </span>
          </div>
        </div>

        {/* ================= SECTION C: RIGHT FLANK (GOTEK BAY) ================= */}
        <div className="flex items-center flex-1 justify-end pr-2">
          <GotekBay
            powerOn={state.powerOn}
            selectedDisk={selectedDisk}
            mountedDisk={mountedDisk}
            diskList={diskList}
            selectedDiskIndex={state.gotek.selectedImageIndex}
            isDiskBusy={state.gotek.isBusy}
            diskTrack={state.gotek.currentTrack}
            usbInserted={state.gotek.usbInserted}
            onSelectDiskIndex={onSelectDiskIndex}
            onMountDisk={onMountDisk}
            onToggleUsb={onToggleUsb}
            onEventEmit={onEventEmit}
          />
        </div>

        {/* RIGHT RACK EAR */}
        <RackEar side="right" />
      </div>
    </div>
  );
};
