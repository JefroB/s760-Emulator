import React, { useRef, useState, useEffect } from 'react';
import { SamplerState, SamplerMode, DiskImage } from '../types/sampler';

interface OP760MonitorProps {
  state: SamplerState;
  diskList: DiskImage[];
  onSetMode: (mode: SamplerMode) => void;
  onSoftKey: (index: number) => void;
  onSelectPatchIndex?: (index: number) => void;
  onEventEmit: (type: string, payload: any) => void;
}

export const OP760Monitor: React.FC<OP760MonitorProps> = ({
  state,
  diskList,
  onSetMode,
  onSoftKey,
  onSelectPatchIndex,
  onEventEmit,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 320, y: 120 });
  const [hoveredTab, setHoveredTab] = useState<SamplerMode | null>(null);

  const selectedDisk = diskList[state.gotek.selectedImageIndex] || diskList[0];
  const mountedDisk =
    state.gotek.mountedImageIndex !== null ? diskList[state.gotek.mountedImageIndex] : null;

  const currentDisk = mountedDisk || selectedDisk;
  const patches = currentDisk?.patches || [
    '01 Warm String Ens',
    '02 Orchestral Brass',
    '03 Grand Piano 1',
    '04 Slap Bass & Lead',
    '05 Acoustic Kit 1',
    '06 Analog Synth Pad',
  ];

  const currentPatchName =
    patches[state.currentPatchIndex % patches.length] || '01 Warm String Ens';

  // Handle Mouse movement inside CRT screen
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.floor((e.clientX - rect.left) * scaleX);
    const y = Math.floor((e.clientY - rect.top) * scaleY);
    setMousePos({ x, y });

    // Check header tabs (y: 2 to 20)
    if (y >= 2 && y <= 20) {
      const tabs: SamplerMode[] = ['PERF', 'PATCH', 'PART', 'SAMPLE', 'SYSTEM', 'DISK'];
      const tabWidth = 80;
      const tabIdx = Math.floor((x - 10) / tabWidth);
      if (tabIdx >= 0 && tabIdx < tabs.length) {
        setHoveredTab(tabs[tabIdx]);
      } else {
        setHoveredTab(null);
      }
    } else {
      setHoveredTab(null);
    }
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.floor((e.clientX - rect.left) * scaleX);
    const y = Math.floor((e.clientY - rect.top) * scaleY);

    // Click on Top Menu Tabs
    if (y >= 2 && y <= 22) {
      const tabs: SamplerMode[] = ['PERF', 'PATCH', 'PART', 'SAMPLE', 'SYSTEM', 'DISK'];
      const tabWidth = 80;
      const tabIdx = Math.floor((x - 10) / tabWidth);
      if (tabIdx >= 0 && tabIdx < tabs.length) {
        onSetMode(tabs[tabIdx]);
        onEventEmit('CRT_TAB_CLICK', { mode: tabs[tabIdx] });
        return;
      }
    }

    // Click on Bottom Soft Keys
    if (y >= 218 && y <= 238) {
      const softKeyWidth = 96;
      const softIdx = Math.floor((x - 20) / softKeyWidth);
      if (softIdx >= 0 && softIdx < 6) {
        onSoftKey(softIdx);
        onEventEmit('CRT_SOFTKEY_CLICK', { index: softIdx, key: `F${softIdx + 1}` });
        return;
      }
    }

    // Click on Patch rows in PERF / PATCH mode
    if ((state.mode === 'PERF' || state.mode === 'PATCH') && y >= 40 && y <= 160) {
      const rowIdx = Math.floor((y - 40) / 20);
      if (rowIdx >= 0 && rowIdx < patches.length) {
        if (onSelectPatchIndex) {
          onSelectPatchIndex(rowIdx);
        }
        onEventEmit('CRT_PATCH_ROW_CLICK', { index: rowIdx, patch: patches[rowIdx] });
      }
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = 640;
    const H = 240;

    // Power off CRT
    if (!state.powerOn) {
      ctx.fillStyle = '#06080c';
      ctx.fillRect(0, 0, W, H);
      // Subtle glass glare reflection
      const grad = ctx.createLinearGradient(0, 0, W, H);
      grad.addColorStop(0, 'rgba(255, 255, 255, 0.03)');
      grad.addColorStop(0.5, 'rgba(0, 0, 0, 0)');
      grad.addColorStop(1, 'rgba(255, 255, 255, 0.01)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, W, H);
      return;
    }

    // Roland S-760 Color Palette
    const bgDark = '#000044'; // Classic Roland dark navy blue CRT background
    const bgPanel = '#000066';
    const fgWhite = '#ffffff';
    const fgCyan = '#00ffff';
    const fgYellow = '#ffff00';
    const fgGreen = '#00ff66';
    const fgRed = '#ff3344';
    const barActive = '#0088cc';
    const barInactive = '#002255';

    // Clear background
    ctx.fillStyle = bgDark;
    ctx.fillRect(0, 0, W, H);

    // Draw Top Menu Bar
    ctx.fillStyle = '#001133';
    ctx.fillRect(0, 0, W, 24);
    ctx.fillStyle = '#0055aa';
    ctx.fillRect(0, 23, W, 1);

    const tabs: { id: SamplerMode; label: string }[] = [
      { id: 'PERF', label: 'PERFORM' },
      { id: 'PATCH', label: 'PATCH' },
      { id: 'PART', label: 'PART' },
      { id: 'SAMPLE', label: 'SAMPLE' },
      { id: 'SYSTEM', label: 'SYSTEM' },
      { id: 'DISK', label: 'DISK' },
    ];

    tabs.forEach((tab, idx) => {
      const tabX = 10 + idx * 80;
      const isActive = state.mode === tab.id;
      const isHover = hoveredTab === tab.id;

      if (isActive) {
        ctx.fillStyle = barActive;
        ctx.fillRect(tabX, 2, 74, 21);
        ctx.strokeStyle = fgCyan;
        ctx.strokeRect(tabX, 2, 74, 21);
        ctx.fillStyle = fgWhite;
      } else if (isHover) {
        ctx.fillStyle = '#003366';
        ctx.fillRect(tabX, 2, 74, 21);
        ctx.fillStyle = fgCyan;
      } else {
        ctx.fillStyle = barInactive;
        ctx.fillRect(tabX, 2, 74, 21);
        ctx.fillStyle = '#88aacc';
      }

      ctx.font = 'bold 10px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(tab.label, tabX + 37, 13);
    });

    // Right status indicator (Roland Logo & Gotek Status)
    ctx.textAlign = 'right';
    ctx.font = 'bold 10px monospace';
    ctx.fillStyle = fgYellow;
    ctx.fillText('Roland S-760', W - 14, 13);

    // Main Content Area based on Mode
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';

    if (state.gotek.isBusy) {
      // Disk Loading Overlay
      ctx.fillStyle = 'rgba(0, 0, 50, 0.9)';
      ctx.fillRect(40, 40, W - 80, 160);
      ctx.strokeStyle = fgCyan;
      ctx.lineWidth = 2;
      ctx.strokeRect(40, 40, W - 80, 160);

      ctx.fillStyle = fgYellow;
      ctx.font = 'bold 14px monospace';
      ctx.fillText('=== GOTEK FLOPPY DMA READ IN PROGRESS ===', 60, 60);

      ctx.fillStyle = fgWhite;
      ctx.font = '12px monospace';
      ctx.fillText(`IMAGE: ${selectedDisk.filename}`, 60, 90);
      ctx.fillText(`TRACK: ${state.gotek.currentTrack.toString().padStart(2, '0')} / 79   [24-BIT INTERNAL DMA BUS]`, 60, 115);

      // Progress bar
      ctx.fillStyle = '#002244';
      ctx.fillRect(60, 145, W - 120, 20);
      ctx.strokeStyle = fgWhite;
      ctx.strokeRect(60, 145, W - 120, 20);

      const ratio = Math.min(1, (state.gotek.currentTrack + 1) / 80);
      ctx.fillStyle = fgCyan;
      ctx.fillRect(62, 147, Math.floor((W - 124) * ratio), 16);
    } else if (state.mode === 'PERF') {
      // Performance Mode
      ctx.fillStyle = bgPanel;
      ctx.fillRect(10, 30, W - 20, 180);
      ctx.strokeStyle = '#004488';
      ctx.strokeRect(10, 30, W - 20, 180);

      ctx.fillStyle = fgYellow;
      ctx.font = 'bold 12px monospace';
      ctx.fillText(`[PERFORMANCE PLAY]  PERF: 01 ORCHESTRAL SUITE`, 20, 38);
      ctx.fillStyle = fgCyan;
      ctx.font = '11px monospace';
      ctx.fillText(`DISK: ${currentDisk?.name || 'NO DISK'} (${currentDisk?.filename || 'EMPTY'})`, 340, 38);

      // Patch List Header
      ctx.fillStyle = '#002255';
      ctx.fillRect(20, 58, W - 40, 16);
      ctx.fillStyle = fgWhite;
      ctx.font = 'bold 10px monospace';
      ctx.fillText('NUM  PATCH NAME             OUT  TVF  TVA  PAN  SPLIT', 26, 62);

      // Patch Rows
      patches.slice(0, 6).forEach((patch, idx) => {
        const rowY = 78 + idx * 19;
        const isSelected = state.currentPatchIndex % patches.length === idx;

        if (isSelected) {
          ctx.fillStyle = '#0066aa';
          ctx.fillRect(20, rowY - 2, W - 40, 18);
          ctx.fillStyle = fgYellow;
        } else {
          ctx.fillStyle = idx % 2 === 0 ? '#001a44' : '#002655';
          ctx.fillRect(20, rowY - 2, W - 40, 18);
          ctx.fillStyle = fgWhite;
        }

        ctx.font = '11px monospace';
        const numStr = (idx + 1).toString().padStart(2, '0');
        const paddedPatch = patch.padEnd(22, ' ').slice(0, 22);
        ctx.fillText(`P${numStr}  ${paddedPatch} 1/2  078  064   C   C1-G7`, 26, rowY + 1);
      });
    } else if (state.mode === 'PATCH') {
      // Patch Edit Mode
      ctx.fillStyle = bgPanel;
      ctx.fillRect(10, 30, W - 20, 180);
      ctx.strokeStyle = '#004488';
      ctx.strokeRect(10, 30, W - 20, 180);

      ctx.fillStyle = fgYellow;
      ctx.font = 'bold 12px monospace';
      ctx.fillText(`[PATCH EDIT]  PATCH: ${currentPatchName}`, 20, 38);

      // TVF / TVA Envelope & Filter Visualizer
      ctx.strokeStyle = fgCyan;
      ctx.strokeRect(20, 60, 280, 140);
      ctx.fillStyle = '#001a33';
      ctx.fillRect(20, 60, 280, 140);

      ctx.fillStyle = fgYellow;
      ctx.font = '10px monospace';
      ctx.fillText('TVF 4-POLE RESONANT FILTER CURVE', 30, 68);

      // Draw Filter curve
      ctx.beginPath();
      ctx.strokeStyle = fgGreen;
      ctx.lineWidth = 2;
      ctx.moveTo(35, 160);
      ctx.lineTo(150, 100);
      ctx.lineTo(180, 80);
      ctx.lineTo(230, 180);
      ctx.lineTo(290, 185);
      ctx.stroke();

      // Right parameter box
      ctx.fillStyle = fgWhite;
      ctx.font = '11px monospace';
      ctx.fillText('CUTOFF FREQ : 078 (3.2 kHz)', 320, 70);
      ctx.fillText('RESONANCE   : 032 (+4.5 dB)', 320, 92);
      ctx.fillText('KEY FOLLOW  : +1.0', 320, 114);
      ctx.fillText('ENV ATTACK  : 014 (12 ms)', 320, 136);
      ctx.fillText('ENV DECAY   : 064 (450 ms)', 320, 158);
      ctx.fillText('OUTPUT ASSIGN: OUT 1/2 (STEREO)', 320, 180);
    } else if (state.mode === 'SAMPLE') {
      // Waveform Mode
      ctx.fillStyle = bgPanel;
      ctx.fillRect(10, 30, W - 20, 180);
      ctx.strokeStyle = '#004488';
      ctx.strokeRect(10, 30, W - 20, 180);

      ctx.fillStyle = fgYellow;
      ctx.font = 'bold 12px monospace';
      ctx.fillText(`[WAVEFORM DISPLAY]  SAMPLE: ${currentPatchName} [ZOOM: ${state.sampleZoom}x]`, 20, 38);

      // Draw Waveform Grid & Sine/Wave visualization
      ctx.fillStyle = '#001122';
      ctx.fillRect(20, 60, W - 40, 140);
      ctx.strokeStyle = '#003366';
      ctx.strokeRect(20, 60, W - 40, 140);

      // Waveform centerline
      ctx.strokeStyle = '#004477';
      ctx.beginPath();
      ctx.moveTo(20, 130);
      ctx.lineTo(W - 20, 130);
      ctx.stroke();

      // Draw synthetic audio wave
      ctx.beginPath();
      ctx.strokeStyle = fgCyan;
      ctx.lineWidth = 1.5;
      for (let x = 20; x < W - 20; x++) {
        const progress = (x - 20) / (W - 40);
        const freq = 12 * state.sampleZoom;
        const amp = 50 * Math.sin(progress * Math.PI) * Math.exp(-progress * 1.5);
        const waveY = 130 + Math.sin(progress * freq * 2 * Math.PI) * amp;
        if (x === 20) ctx.moveTo(x, waveY);
        else ctx.lineTo(x, waveY);
      }
      ctx.stroke();

      // Scrub marker
      const scrubX = 20 + ((W - 40) * state.sampleScrub) / 100;
      ctx.strokeStyle = fgRed;
      ctx.beginPath();
      ctx.moveTo(scrubX, 60);
      ctx.lineTo(scrubX, 200);
      ctx.stroke();
    } else {
      // Generic Mode (DISK / SYSTEM / PART)
      ctx.fillStyle = bgPanel;
      ctx.fillRect(10, 30, W - 20, 180);
      ctx.strokeStyle = '#004488';
      ctx.strokeRect(10, 30, W - 20, 180);

      ctx.fillStyle = fgYellow;
      ctx.font = 'bold 12px monospace';
      ctx.fillText(`[${state.mode} UTILITY]  FLASHFLOPPY GOTEK INTERFACE`, 20, 38);

      ctx.fillStyle = fgWhite;
      ctx.font = '11px monospace';
      ctx.fillText(`SELECTED GOTEK IMAGE : ${selectedDisk.filename}`, 30, 70);
      ctx.fillText(`MOUNTED GOTEK IMAGE  : ${mountedDisk ? mountedDisk.filename : 'NONE'}`, 30, 95);
      ctx.fillText(`DRIVE STATUS         : ${state.gotek.usbInserted ? 'USB MOUNTED' : 'NO MEDIA'}`, 30, 120);
      ctx.fillText(`SCSI BUS ID          : ID #0 (INTERNAL SAMPLER ENGINE)`, 30, 145);
      ctx.fillText(`MEMORY CAPACITY      : 32.0 MB / 32.0 MB INSTALLED`, 30, 170);
    }

    // Bottom Function Keys Strip [F1] to [F6]
    ctx.fillStyle = '#001133';
    ctx.fillRect(0, 216, W, 24);
    ctx.fillStyle = '#0055aa';
    ctx.fillRect(0, 216, W, 1);

    const softKeys = [
      { key: 'F1', label: 'PLAY' },
      { key: 'F2', label: 'ZOOM' },
      { key: 'F3', label: 'LOOP' },
      { key: 'F4', label: 'MARK' },
      { key: 'F5', label: 'COMM' },
      { key: 'F6', label: 'EXIT' },
    ];

    softKeys.forEach((k, idx) => {
      const kX = 20 + idx * 100;
      ctx.fillStyle = '#002b55';
      ctx.fillRect(kX, 219, 90, 18);
      ctx.strokeStyle = '#005599';
      ctx.strokeRect(kX, 219, 90, 18);

      ctx.font = 'bold 10px monospace';
      ctx.fillStyle = fgYellow;
      ctx.fillText(`[${k.key}]`, kX + 6, 224);
      ctx.fillStyle = fgWhite;
      ctx.fillText(k.label, kX + 38, 224);
    });

    // Draw Roland Mouse Cursor
    if (state.powerOn) {
      const { x, y } = mousePos;
      ctx.fillStyle = fgWhite;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x, y + 14);
      ctx.lineTo(x + 4, y + 10);
      ctx.lineTo(x + 10, y + 10);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }, [state, diskList, selectedDisk, mountedDisk, mousePos, hoveredTab, patches, currentPatchName]);

  return (
    <div className="relative flex flex-col items-center select-none">
      {/* Authentic Retro OP-760 Color CRT Monitor Bezel */}
      <div className="relative p-4 rounded-xl bg-gradient-to-b from-[#2a2d33] via-[#1b1d22] to-[#121417] border-4 border-[#3c414a] shadow-[0_20px_60px_rgba(0,0,0,0.95),inset_0_2px_4px_rgba(255,255,255,0.2)]">
        {/* Monitor Brand Silk-screen */}
        <div className="flex items-center justify-between pb-1.5 px-2 text-neutral-400 font-mono text-[9px] uppercase tracking-wider">
          <span className="font-bold text-neutral-200">Roland OP-760 COLOR MONITOR</span>
          <span className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${state.powerOn ? 'bg-emerald-400 shadow-[0_0_6px_#34d399]' : 'bg-neutral-600'}`} />
            RGB / S-VIDEO
          </span>
        </div>

        {/* CRT Glass Screen Container with Curvature & Scanlines */}
        <div className="relative overflow-hidden rounded-lg bg-black border-2 border-neutral-800 shadow-[inset_0_0_20px_rgba(0,0,0,0.9)]">
          <canvas
            ref={canvasRef}
            width={640}
            height={240}
            onMouseMove={handleMouseMove}
            onClick={handleCanvasClick}
            className="w-[720px] h-[270px] sm:w-[800px] sm:h-[300px] lg:w-[960px] lg:h-[360px] cursor-crosshair block"
          />

          {/* CRT Scanline Overlay */}
          <div
            className="absolute inset-0 pointer-events-none opacity-25"
            style={{
              background:
                'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.4) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.04), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.04))',
              backgroundSize: '100% 3px, 6px 100%',
            }}
          />

          {/* CRT Glass Curvature Highlight */}
          <div
            className="absolute inset-0 pointer-events-none opacity-20"
            style={{
              background:
                'radial-gradient(ellipse at 50% 30%, rgba(255, 255, 255, 0.3) 0%, rgba(0, 0, 0, 0.4) 80%, rgba(0, 0, 0, 0.8) 100%)',
            }}
          />
        </div>
      </div>
    </div>
  );
};
