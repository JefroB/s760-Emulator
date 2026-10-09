import React, { useEffect, useRef } from 'react';
import { SamplerMode, DiskImage } from '../types/sampler';
import { useSurfaceCanvas, backlightTint } from '../bridge/BridgeContext';
import { SurfaceId, LCD_WIDTH as BRIDGE_LCD_WIDTH, LCD_HEIGHT as BRIDGE_LCD_HEIGHT } from '../bridge/S760BridgeClient';

interface RolandLCDProps {
  powerOn: boolean;
  mode: SamplerMode;
  backlightColor: 'emerald' | 'amber';
  activePatchName: string;
  mountedDisk: DiskImage | null;
  selectedDisk: DiskImage;
  isDiskBusy: boolean;
  diskTrack: number;
  sampleZoom: number;
  sampleScrub: number;
  volume: number;
  activeCursorField: number;
  onSoftKeyClick?: (fIndex: number) => void;
}

export const RolandLCD: React.FC<RolandLCDProps> = ({
  powerOn,
  mode,
  backlightColor,
  activePatchName,
  mountedDisk,
  selectedDisk,
  isDiskBusy,
  diskTrack,
  sampleZoom,
  sampleScrub,
  volume,
  activeCursorField,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  // Live SED1335 160x64 buffer from the bridge (MONO1), tinted to the selected
  // backlight color (R6.2). Blitted imperatively with no per-frame React state;
  // overlays the offline canvas and is transparent until the first frame.
  const lcdLiveRef = useSurfaceCanvas(SurfaceId.LCD, {
    tint: backlightTint(backlightColor),
  });

  // 160 x 64 native S-760 LCD resolution
  const LCD_WIDTH = 160;
  const LCD_HEIGHT = 64;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Palette configuration
    const isEmerald = backlightColor === 'emerald';
    const bgCol = powerOn
      ? isEmerald
        ? '#132c10'
        : '#2b1a06'
      : '#0d130c';
    const fgCol = powerOn
      ? isEmerald
        ? '#73ff38'
        : '#ffaa24'
      : '#1a2418';
    const dimCol = powerOn
      ? isEmerald
        ? 'rgba(115, 255, 56, 0.22)'
        : 'rgba(255, 170, 36, 0.22)'
      : 'rgba(26, 36, 24, 0.2)';

    // Clear background
    ctx.fillStyle = bgCol;
    ctx.fillRect(0, 0, LCD_WIDTH, LCD_HEIGHT);

    if (!powerOn) {
      // Draw faint unpowered grid
      ctx.fillStyle = 'rgba(0,0,0,0.45)';
      ctx.fillRect(0, 0, LCD_WIDTH, LCD_HEIGHT);
      return;
    }

    // Helper: Draw 5x7 or 3x5 bitmap style text
    ctx.font = '8px monospace';
    ctx.textBaseline = 'top';

    if (isDiskBusy) {
      // Floppy / Gotek Loading Screen
      ctx.fillStyle = fgCol;
      ctx.fillText('== DISK READ IN PROGRESS ==', 8, 4);

      ctx.fillStyle = dimCol;
      ctx.fillRect(8, 16, 144, 18);
      ctx.strokeStyle = fgCol;
      ctx.strokeRect(8, 16, 144, 18);

      // Loading progress bar
      const progressRatio = Math.min(1, (diskTrack + 1) / 80);
      ctx.fillStyle = fgCol;
      ctx.fillRect(10, 18, Math.floor(140 * progressRatio), 14);

      ctx.fillText(`IMG: ${selectedDisk.filename}`, 8, 38);
      ctx.fillText(`TRACK ${diskTrack.toString().padStart(2, '0')}/79   24-BIT DMA`, 8, 48);

      // Bottom bar
      ctx.fillStyle = dimCol;
      ctx.fillRect(0, 56, 160, 8);
      ctx.fillStyle = fgCol;
      ctx.fillText('BUSY... DO NOT POWER OFF', 8, 56);
      return;
    }

    // Draw header bar
    ctx.fillStyle = dimCol;
    ctx.fillRect(0, 0, LCD_WIDTH, 10);
    ctx.fillStyle = fgCol;

    const modeLabels: Record<SamplerMode, string> = {
      PERF: 'PERFORMANCE PLAY',
      PATCH: 'PATCH EDIT (TVF/TVA)',
      PART: 'PART MULTI-TIMBRAL',
      SAMPLE: 'WAVEFORM DISPLAY',
      SYSTEM: 'SYSTEM / SCSI SETUP',
      DISK: 'DISK / GOTEK UTILITY',
    };

    ctx.fillText(modeLabels[mode], 4, 1);
    ctx.fillText(`${volume}%`, 136, 1);

    // Render mode specific screen
    if (mode === 'PERF') {
      ctx.fillStyle = fgCol;
      ctx.fillText(`P01: ${activePatchName}`, 4, 13);

      ctx.fillStyle = activeCursorField === 0 ? dimCol : 'transparent';
      ctx.fillRect(4, 23, 152, 9);
      ctx.fillStyle = fgCol;
      ctx.fillText(`PT1: 01 Warm Str  VOL:100 PAN:C`, 6, 24);

      ctx.fillStyle = activeCursorField === 1 ? dimCol : 'transparent';
      ctx.fillRect(4, 33, 152, 9);
      ctx.fillStyle = fgCol;
      ctx.fillText(`PT2: 02 Fr Horn   VOL:085 PAN:R`, 6, 34);

      ctx.fillStyle = activeCursorField === 2 ? dimCol : 'transparent';
      ctx.fillRect(4, 43, 152, 9);
      ctx.fillStyle = fgCol;
      ctx.fillText(`PT3: 03 Ac Bass   VOL:090 PAN:L`, 6, 44);

      // Soft keys footer
      drawFooter(ctx, ['TUNE', 'MIDI', 'INIT', 'NAME', 'COMM', 'EXIT'], fgCol, dimCol);

    } else if (mode === 'PATCH') {
      ctx.fillStyle = fgCol;
      ctx.fillText(`PATCH: ${activePatchName}`, 4, 13);
      ctx.fillText(`TVF CUTOFF: 078   RESO: 032`, 4, 24);
      ctx.fillText(`TVA ATTACK: 014   REL : 062`, 4, 34);
      ctx.fillText(`SPLIT: C1-G7      ROUTE: OUT 1/2`, 4, 44);

      drawFooter(ctx, ['TVF', 'TVA', 'LFO', 'ZONE', 'COPY', 'EXIT'], fgCol, dimCol);

    } else if (mode === 'SAMPLE') {
      // Waveform display
      ctx.fillStyle = fgCol;
      ctx.fillText(`WAV: ${selectedDisk.sampleWaveformType.toUpperCase()}  ${selectedDisk.sampleRate}`, 4, 12);
      ctx.fillText(`ZOOM: ${sampleZoom}x  SCRUB: ${sampleScrub}%`, 94, 12);

      // Draw audio waveform area
      const waveY = 22;
      const waveH = 26;
      ctx.fillStyle = dimCol;
      ctx.fillRect(4, waveY, 152, waveH);
      ctx.strokeStyle = fgCol;
      ctx.strokeRect(4, waveY, 152, waveH);

      // Center baseline
      const midY = waveY + waveH / 2;
      ctx.beginPath();
      ctx.moveTo(4, midY);
      ctx.lineTo(156, midY);
      ctx.strokeStyle = dimCol;
      ctx.stroke();

      // Draw waveform shape
      ctx.beginPath();
      ctx.strokeStyle = fgCol;
      for (let x = 0; x < 150; x++) {
        const norm = (x + sampleScrub * 0.5) * sampleZoom * 0.08;
        let amp = 0;
        if (selectedDisk.sampleWaveformType === 'strings') {
          amp = Math.sin(norm * 1.5) * 8 + Math.sin(norm * 4.2) * 4;
        } else if (selectedDisk.sampleWaveformType === 'brass') {
          amp = Math.sin(norm * 2.1) * 10 * Math.exp(-((x % 30) / 25));
        } else if (selectedDisk.sampleWaveformType === 'drum') {
          amp = Math.sin(norm * 3.5) * 11 * Math.exp(-((x % 40) / 15));
        } else if (selectedDisk.sampleWaveformType === 'bass') {
          amp = (Math.sin(norm) + Math.sin(norm * 2) * 0.5) * 10;
        } else {
          amp = Math.sin(norm * 2.8) * 9;
        }
        const py = midY + Math.max(-12, Math.min(12, amp));
        if (x === 0) ctx.moveTo(5 + x, py);
        else ctx.lineTo(5 + x, py);
      }
      ctx.stroke();

      // Loop point markers
      const loopStartX = 28;
      const loopEndX = 130;
      ctx.fillStyle = fgCol;
      ctx.fillRect(loopStartX, waveY, 1, waveH);
      ctx.fillText('S', loopStartX + 2, waveY + 1);

      ctx.fillRect(loopEndX, waveY, 1, waveH);
      ctx.fillText('E', loopEndX - 7, waveY + 1);

      drawFooter(ctx, ['AUDN', 'ZOOM', 'LOOP', 'MARK', 'COMM', 'EXIT'], fgCol, dimCol);

    } else if (mode === 'DISK') {
      ctx.fillStyle = fgCol;
      ctx.fillText(`FD: GOTEK USB [FF-OS]`, 4, 13);
      ctx.fillText(`IMG: ${mountedDisk ? mountedDisk.filename : '(NO DISK MOUNTED)'}`, 4, 23);
      ctx.fillText(`SIZE: ${selectedDisk.sizeKb}KB  FMT: ${selectedDisk.format}`, 4, 33);
      ctx.fillText(`LOAD ALL PATCHES -> INT RAM`, 4, 43);

      drawFooter(ctx, ['LOAD', 'SAVE', 'DIR', 'INFO', 'EJCT', 'EXIT'], fgCol, dimCol);

    } else if (mode === 'PART') {
      ctx.fillStyle = fgCol;
      ctx.fillText(`MULTI: 32-VOICE DYNAMIC`, 4, 13);
      ctx.fillText(`PT1: CH01  STR  OUT:1/2`, 4, 23);
      ctx.fillText(`PT2: CH02  BRS  OUT:3/4`, 4, 33);
      ctx.fillText(`PT3: CH03  BAS  OUT:DIR`, 4, 43);

      drawFooter(ctx, ['MUTE', 'SOLO', 'OUT', 'PAN', 'FX', 'EXIT'], fgCol, dimCol);

    } else if (mode === 'SYSTEM') {
      ctx.fillStyle = fgCol;
      ctx.fillText(`MASTER TUNE: 440.0 Hz`, 4, 13);
      ctx.fillText(`SCSI ID: #7   MOUSE: ENABLED`, 4, 23);
      ctx.fillText(`BACKLIGHT: ${isEmerald ? 'EMERALD GREEN' : 'AMBER ORANGE'}`, 4, 33);
      ctx.fillText(`INT RAM: 32MB EXPANSION OK`, 4, 43);

      drawFooter(ctx, ['CALIB', 'SCSI', 'TEST', 'COLOR', 'RST', 'EXIT'], fgCol, dimCol);
    }
  }, [
    powerOn,
    mode,
    backlightColor,
    activePatchName,
    mountedDisk,
    selectedDisk,
    isDiskBusy,
    diskTrack,
    sampleZoom,
    sampleScrub,
    volume,
    activeCursorField,
  ]);

  function drawFooter(
    ctx: CanvasRenderingContext2D,
    keys: string[],
    fg: string,
    dim: string
  ) {
    ctx.fillStyle = dim;
    ctx.fillRect(0, 54, 160, 10);
    ctx.fillStyle = fg;
    const colWidth = 160 / 6;
    keys.forEach((k, i) => {
      ctx.fillText(k, Math.floor(i * colWidth + 2), 55);
      if (i < 5) {
        ctx.fillStyle = dim;
        ctx.fillRect(Math.floor((i + 1) * colWidth), 54, 1, 10);
        ctx.fillStyle = fg;
      }
    });
  }

  const isEmerald = backlightColor === 'emerald';

  return (
    <div className="relative flex flex-col items-center">
      {/* Recessed bezel housing */}
      <div
        className={`relative p-1 rounded-sm bg-neutral-900 border border-neutral-700/80 shadow-[inset_0_2px_5px_rgba(0,0,0,0.9),0_1px_1px_rgba(255,255,255,0.06)]`}
        style={{
          boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.95), 0 1px 1px rgba(255,255,255,0.08)',
        }}
      >
        {/* Recessed acrylic frame */}
        <div
          className={`relative overflow-hidden rounded-[2px] transition-all duration-300 ${
            powerOn
              ? isEmerald
                ? 'lcd-green-glow border border-emerald-500/40 bg-[#12280f]'
                : 'lcd-amber-glow border border-amber-500/40 bg-[#281805]'
              : 'border border-neutral-800 bg-[#090e08]'
          }`}
          style={{ width: '240px', height: '96px' }}
        >
          {/* Native 160x64 Canvas Scaled */}
          <canvas
            ref={canvasRef}
            width={LCD_WIDTH}
            height={LCD_HEIGHT}
            className="w-full h-full object-fill [image-rendering:pixelated]"
          />

          {/* Live SED1335 buffer from the bridge (R6.2). Transparent until the
              first frame so the offline canvas shows through when disconnected. */}
          <canvas
            ref={lcdLiveRef}
            width={BRIDGE_LCD_WIDTH}
            height={BRIDGE_LCD_HEIGHT}
            className="pointer-events-none absolute inset-0 w-full h-full object-fill [image-rendering:pixelated]"
          />

          {/* Authentic scanline & LCD dot-matrix subtle overlay */}
          <div
            className="pointer-events-none absolute inset-0 opacity-20 mix-blend-overlay"
            style={{
              backgroundImage:
                'repeating-linear-gradient(0deg, rgba(0,0,0,0.4) 0px, rgba(0,0,0,0.4) 1px, transparent 1px, transparent 2px), repeating-linear-gradient(90deg, rgba(0,0,0,0.3) 0px, rgba(0,0,0,0.3) 1px, transparent 1px, transparent 2px)',
            }}
          />

          {/* Acrylic diagonal glare reflection */}
          <div className="pointer-events-none absolute inset-0 acrylic-reflection" />
        </div>
      </div>
    </div>
  );
};
