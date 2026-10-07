import React, { useState, useRef, useEffect } from 'react';
import { DiskImage } from '../types/sampler';
import { soundFx } from '../audio/soundFx';

interface GotekBayProps {
  powerOn: boolean;
  selectedDisk: DiskImage;
  mountedDisk: DiskImage | null;
  diskList: DiskImage[];
  selectedDiskIndex: number;
  isDiskBusy: boolean;
  diskTrack: number;
  usbInserted: boolean;
  onSelectDiskIndex: (idx: number) => void;
  onMountDisk: () => void;
  onToggleUsb: () => void;
  onEventEmit: (type: string, payload: any) => void;
}

export const GotekBay: React.FC<GotekBayProps> = ({
  powerOn,
  selectedDisk,
  mountedDisk,
  diskList,
  selectedDiskIndex,
  isDiskBusy,
  diskTrack,
  usbInserted,
  onSelectDiskIndex,
  onMountDisk,
  onToggleUsb,
  onEventEmit,
}) => {
  const [knobAngle, setKnobAngle] = useState(0);
  const [isKnobPressed, setIsKnobPressed] = useState(false);
  const [prevPressed, setPrevPressed] = useState(false);
  const [nextPressed, setNextPressed] = useState(false);
  const [selPressed, setSelPressed] = useState(false);
  const dragStartY = useRef<number | null>(null);
  const initialAngle = useRef<number>(0);

  // Mouse wheel rotation on encoder knob
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (!powerOn || !usbInserted) return;
    const delta = e.deltaY > 0 ? 1 : -1;
    stepDisk(delta);
  };

  // Drag rotation on encoder knob
  const handleMouseDownKnob = (e: React.MouseEvent) => {
    if (!powerOn) return;
    dragStartY.current = e.clientY;
    initialAngle.current = knobAngle;
    setIsKnobPressed(true);
    soundFx.playClick('gotek_dial');

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (dragStartY.current === null) return;
      const dy = dragStartY.current - moveEvent.clientY;
      const steps = Math.trunc(dy / 14);
      if (steps !== 0) {
        stepDisk(steps > 0 ? 1 : -1);
        dragStartY.current = moveEvent.clientY;
      }
    };

    const handleMouseUp = () => {
      dragStartY.current = null;
      setIsKnobPressed(false);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const stepDisk = (direction: number) => {
    if (!usbInserted) return;
    const newIdx = (selectedDiskIndex + direction + diskList.length) % diskList.length;
    setKnobAngle((prev) => prev + direction * 30);
    soundFx.playClick('gotek_dial');
    onSelectDiskIndex(newIdx);
    onEventEmit('GOTEK_ENCODER_STEP', {
      direction: direction > 0 ? 'UP' : 'DOWN',
      newIndex: newIdx,
      diskName: diskList[newIdx].filename,
    });
  };

  const handlePrevClick = () => {
    if (!powerOn || !usbInserted) return;
    setPrevPressed(true);
    setTimeout(() => setPrevPressed(false), 140);
    soundFx.playClick('button');
    stepDisk(-1);
    onEventEmit('GOTEK_BTN_PREV', { targetDisk: selectedDisk.filename });
  };

  const handleNextClick = () => {
    if (!powerOn || !usbInserted) return;
    setNextPressed(true);
    setTimeout(() => setNextPressed(false), 140);
    soundFx.playClick('button');
    stepDisk(1);
    onEventEmit('GOTEK_BTN_NEXT', { targetDisk: selectedDisk.filename });
  };

  const handleSelClick = () => {
    if (!powerOn || !usbInserted) return;
    setSelPressed(true);
    setTimeout(() => setSelPressed(false), 160);
    soundFx.playClick('button');
    onMountDisk();
    onEventEmit('GOTEK_BTN_SEL', { mountedDisk: selectedDisk.filename });
  };

  const isMountedCurrent = mountedDisk?.id === selectedDisk.id;

  return (
    <div className="relative flex flex-col justify-center h-full px-2 py-1 select-none">
      {/* 3.5" Floppy Bay Bezel Outer Frame */}
      <div
        className="relative flex items-center justify-between px-2.5 py-1.5 rounded-[3px] bg-gradient-to-b from-[#111317] via-[#16181d] to-[#0c0d10] border border-neutral-700/60 shadow-[inset_0_2px_4px_rgba(0,0,0,0.9),0_1px_1px_rgba(255,255,255,0.06)]"
        style={{ width: '272px', height: '102px' }}
      >
        {/* Subtle Gotek Metal Silkscreen Badge */}
        <div className="absolute top-1 left-2.5 flex items-center gap-1.5 pointer-events-none">
          <span className="text-[7.5px] font-mono tracking-wider text-neutral-400/80 font-bold uppercase">
            Gotek SFR1M44-U100K
          </span>
          <span className="text-[6.5px] font-mono text-cyan-500/70 tracking-widest uppercase">
            FlashFloppy 3.42
          </span>
        </div>

        {/* Left Side: 128x32 / 128x64 OLED Display & Micro LEDs */}
        <div className="flex flex-col gap-1.5 mt-2">
          {/* FlashFloppy I2C OLED Screen */}
          <div
            className={`relative flex flex-col justify-center px-1.5 py-1 rounded-[2px] border transition-colors duration-200 overflow-hidden ${
              powerOn && usbInserted
                ? 'bg-[#03070b] border-cyan-500/50 oled-cyan-glow'
                : 'bg-[#020305] border-neutral-800'
            }`}
            style={{ width: '136px', height: '44px' }}
          >
            {powerOn && usbInserted ? (
              <div className="font-mono text-cyan-300 leading-tight">
                {/* OLED Line 1: Slot / Filename */}
                <div className="text-[8.5px] font-bold tracking-tight truncate drop-shadow-[0_0_4px_rgba(0,242,255,0.8)]">
                  {selectedDisk.slot} {selectedDisk.filename}
                </div>

                {/* OLED Line 2: Track / Status */}
                <div className="text-[7.5px] text-cyan-400/90 tracking-wide flex justify-between items-center mt-1">
                  <span>
                    T:{diskTrack.toString().padStart(2, '0')}.{isDiskBusy ? (diskTrack % 2) : 0}{' '}
                    {isDiskBusy ? 'RD' : 'ST'}
                  </span>
                  <span
                    className={`px-1 py-[0.5px] text-[6.5px] rounded-[1px] font-bold uppercase ${
                      isDiskBusy
                        ? 'bg-amber-400 text-black animate-pulse'
                        : isMountedCurrent
                        ? 'bg-cyan-400/90 text-black'
                        : 'text-cyan-400 border border-cyan-500/40'
                    }`}
                  >
                    {isDiskBusy ? 'BUSY' : isMountedCurrent ? 'MOUNTED' : 'READY'}
                  </span>
                </div>
              </div>
            ) : powerOn && !usbInserted ? (
              <div className="font-mono text-center text-cyan-400/70 text-[8px] animate-pulse">
                * NO USB DRIVE *
                <div className="text-[6.5px] text-cyan-600 mt-0.5">INSERT THUMBDRIVE</div>
              </div>
            ) : (
              <div className="w-full h-full bg-[#020406] opacity-30" />
            )}

            {/* OLED Glass Reflection */}
            <div className="pointer-events-none absolute inset-0 acrylic-reflection opacity-40" />
          </div>

          {/* Micro Activity LEDs & Silkscreen text */}
          <div className="flex items-center justify-between px-0.5">
            <div className="flex items-center gap-1.5">
              {/* Green Power LED */}
              <div className="flex items-center gap-1">
                <div
                  className={`w-2 h-2 rounded-full border border-neutral-900 transition-all duration-150 ${
                    powerOn
                      ? 'bg-emerald-400 shadow-[0_0_6px_#34d399,inset_0_1px_1px_#a7f3d0]'
                      : 'bg-emerald-950/40'
                  }`}
                />
                <span className="text-[6.5px] font-mono text-neutral-400 tracking-wider">PWR</span>
              </div>

              {/* Red/Amber Drive Activity LED */}
              <div className="flex items-center gap-1">
                <div
                  className={`w-2 h-2 rounded-full border border-neutral-900 transition-all duration-75 ${
                    isDiskBusy
                      ? 'bg-amber-400 shadow-[0_0_7px_#f59e0b,inset_0_1px_1px_#fde68a]'
                      : powerOn && isMountedCurrent
                      ? 'bg-amber-800/40'
                      : 'bg-amber-950/30'
                  }`}
                />
                <span className="text-[6.5px] font-mono text-neutral-400 tracking-wider">ACT</span>
              </div>
            </div>

            {/* Tactile buttons under OLED */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handlePrevClick}
                title="Previous Image / Directory [<]"
                className={`w-5 h-4 text-[7px] font-mono font-bold text-neutral-300 rounded-[2px] bg-gradient-to-b from-neutral-700 to-neutral-850 border border-neutral-600 transition-transform ${
                  prevPressed ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110 active:scale-95'
                }`}
              >
                &lt;
              </button>

              <button
                type="button"
                onClick={handleNextClick}
                title="Next Image / Directory [>]"
                className={`w-5 h-4 text-[7px] font-mono font-bold text-neutral-300 rounded-[2px] bg-gradient-to-b from-neutral-700 to-neutral-850 border border-neutral-600 transition-transform ${
                  nextPressed ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110 active:scale-95'
                }`}
              >
                &gt;
              </button>

              <button
                type="button"
                onClick={handleSelClick}
                title="Mount / Select Disk [SEL]"
                className={`px-1.5 h-4 text-[6.5px] font-mono font-bold text-cyan-300 rounded-[2px] bg-gradient-to-b from-neutral-700 to-neutral-850 border border-cyan-800/60 transition-transform ${
                  selPressed ? 'tactile-btn-pressed' : 'tactile-btn hover:brightness-110 active:scale-95'
                }`}
              >
                SEL
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Knurled Encoder Knob & Horizontal USB Type-A port */}
        <div className="flex flex-col items-center justify-between h-full pt-2">
          {/* Knurled Gotek Rotary Encoder Dial with Push-to-Click */}
          <div className="flex flex-col items-center">
            <div
              onWheel={handleWheel}
              onMouseDown={handleMouseDownKnob}
              title="Gotek Rotary Encoder (Scroll or Drag to cycle images, Click to Select)"
              className={`relative cursor-grab active:cursor-grabbing rounded-full border border-neutral-600 shadow-[0_3px_6px_rgba(0,0,0,0.8),inset_0_1px_2px_rgba(255,255,255,0.4)] transition-transform ${
                isKnobPressed ? 'scale-95 shadow-[inset_0_2px_4px_rgba(0,0,0,0.9)]' : 'hover:brightness-110'
              }`}
              style={{
                width: '32px',
                height: '32px',
                background:
                  'radial-gradient(circle at 40% 40%, #70757d 0%, #3a3d44 60%, #1c1d21 100%)',
              }}
            >
              {/* Outer knurled rim pattern */}
              <div
                className="absolute inset-0 rounded-full opacity-60 bg-knurled-rim"
                style={{
                  transform: `rotate(${knobAngle}deg)`,
                  transition: isKnobPressed ? 'none' : 'transform 0.1s ease-out',
                }}
              />
              {/* Center machined cap */}
              <div className="absolute inset-1 rounded-full bg-gradient-to-tr from-neutral-800 via-neutral-600 to-neutral-400 border border-neutral-700 flex items-center justify-center">
                {/* Visual marker notch */}
                <div
                  className="w-1 h-3 bg-cyan-400/90 rounded-full shadow-[0_0_3px_#22d3ee]"
                  style={{
                    transform: `rotate(${knobAngle}deg) translateY(-8px)`,
                    transformOrigin: '50% 12px',
                  }}
                />
              </div>
            </div>
            <span className="text-[6px] font-mono text-neutral-400 font-semibold tracking-tighter mt-0.5">
              [PUSH SEL]
            </span>
          </div>

          {/* USB Type-A Port with low profile thumbdrive */}
          <div className="flex flex-col items-center mt-1">
            <div
              onClick={() => {
                soundFx.playClick('eject');
                onToggleUsb();
                onEventEmit('GOTEK_USB_TOGGLE', { usbInserted: !usbInserted });
              }}
              title={usbInserted ? 'Click to Eject USB Drive' : 'Click to Insert USB Drive'}
              className="relative cursor-pointer group flex items-center justify-center"
            >
              {/* Port cutout */}
              <div className="w-11 h-3 rounded-[1px] bg-black border border-neutral-700 shadow-inner flex items-center justify-center overflow-hidden">
                {usbInserted ? (
                  /* Inserted low-profile metal thumb drive */
                  <div className="relative w-9 h-2.5 rounded-[1px] bg-gradient-to-r from-neutral-400 via-neutral-200 to-neutral-500 border border-neutral-400 shadow-sm flex items-center justify-between px-1">
                    <span className="text-[5px] font-mono font-bold text-neutral-800 tracking-tighter">
                      SANDISK
                    </span>
                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-600/70" />
                  </div>
                ) : (
                  /* Empty USB metal socket contacts */
                  <div className="w-8 h-2 bg-neutral-900 border border-neutral-800 flex items-center justify-center">
                    <div className="w-6 h-0.5 bg-neutral-600" />
                  </div>
                )}
              </div>
            </div>
            <span className="text-[6px] font-mono text-neutral-400 uppercase tracking-tight">
              {usbInserted ? 'USB READY' : 'EMPTY PORT'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
