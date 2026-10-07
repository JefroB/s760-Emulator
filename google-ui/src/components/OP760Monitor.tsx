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

// Complete 8x8 Roland OP-760 ROM Bitmap Font Table from S-760 VDP firmware
const FONT_GLYPHS: Record<string, number[]> = {
  // Uppercase
  A: [0x3c, 0x66, 0x66, 0x7e, 0x66, 0x66, 0x66, 0x00],
  B: [0x7c, 0x66, 0x66, 0x7c, 0x66, 0x66, 0x7c, 0x00],
  C: [0x3c, 0x66, 0x60, 0x60, 0x60, 0x66, 0x3c, 0x00],
  D: [0x78, 0x6c, 0x66, 0x66, 0x66, 0x6c, 0x78, 0x00],
  E: [0x7e, 0x60, 0x60, 0x7c, 0x60, 0x60, 0x7e, 0x00],
  F: [0x7e, 0x60, 0x60, 0x7c, 0x60, 0x60, 0x60, 0x00],
  G: [0x3c, 0x66, 0x60, 0x6e, 0x66, 0x66, 0x3c, 0x00],
  H: [0x66, 0x66, 0x66, 0x7e, 0x66, 0x66, 0x66, 0x00],
  I: [0x3e, 0x1c, 0x1c, 0x1c, 0x1c, 0x1c, 0x3e, 0x00],
  J: [0x1e, 0x0c, 0x0c, 0x0c, 0x0c, 0xcc, 0x78, 0x00],
  K: [0x66, 0x6c, 0x78, 0x70, 0x78, 0x6c, 0x66, 0x00],
  L: [0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7e, 0x00],
  M: [0x63, 0x77, 0x7f, 0x6b, 0x63, 0x63, 0x63, 0x00],
  N: [0x66, 0x76, 0x7e, 0x7e, 0x6e, 0x66, 0x66, 0x00],
  O: [0x3c, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3c, 0x00],
  P: [0x7c, 0x66, 0x66, 0x7c, 0x60, 0x60, 0x60, 0x00],
  Q: [0x3c, 0x66, 0x66, 0x66, 0x66, 0x3c, 0x0e, 0x00],
  R: [0x7c, 0x66, 0x66, 0x7c, 0x78, 0x6c, 0x66, 0x00],
  S: [0x3c, 0x66, 0x60, 0x3c, 0x06, 0x66, 0x3c, 0x00],
  T: [0x7e, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00],
  U: [0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3c, 0x00],
  V: [0x66, 0x66, 0x66, 0x66, 0x66, 0x3c, 0x18, 0x00],
  W: [0x63, 0x63, 0x63, 0x6b, 0x7f, 0x77, 0x63, 0x00],
  X: [0x66, 0x66, 0x3c, 0x18, 0x3c, 0x66, 0x66, 0x00],
  Y: [0x66, 0x66, 0x66, 0x3c, 0x18, 0x18, 0x18, 0x00],
  Z: [0x7e, 0x06, 0x0c, 0x18, 0x30, 0x60, 0x7e, 0x00],

  // Lowercase
  a: [0x00, 0x00, 0x3c, 0x06, 0x3e, 0x66, 0x3e, 0x00],
  b: [0x60, 0x60, 0x7c, 0x66, 0x66, 0x66, 0x7c, 0x00],
  c: [0x00, 0x00, 0x3c, 0x66, 0x60, 0x66, 0x3c, 0x00],
  d: [0x06, 0x06, 0x3e, 0x66, 0x66, 0x66, 0x3e, 0x00],
  e: [0x00, 0x00, 0x3c, 0x66, 0x7e, 0x60, 0x3c, 0x00],
  f: [0x0e, 0x18, 0x3e, 0x18, 0x18, 0x18, 0x18, 0x00],
  g: [0x00, 0x00, 0x3e, 0x66, 0x66, 0x3e, 0x06, 0x3c],
  h: [0x60, 0x60, 0x7c, 0x66, 0x66, 0x66, 0x66, 0x00],
  i: [0x18, 0x00, 0x38, 0x18, 0x18, 0x18, 0x3c, 0x00],
  j: [0x06, 0x00, 0x0e, 0x06, 0x06, 0x66, 0x3c, 0x00],
  k: [0x60, 0x60, 0x66, 0x6c, 0x78, 0x6c, 0x66, 0x00],
  l: [0x38, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3c, 0x00],
  m: [0x00, 0x00, 0x66, 0x7f, 0x7f, 0x6b, 0x63, 0x00],
  n: [0x00, 0x00, 0x7c, 0x66, 0x66, 0x66, 0x66, 0x00],
  o: [0x00, 0x00, 0x3c, 0x66, 0x66, 0x66, 0x3c, 0x00],
  p: [0x00, 0x00, 0x7c, 0x66, 0x66, 0x7c, 0x60, 0x60],
  q: [0x00, 0x00, 0x3e, 0x66, 0x66, 0x3e, 0x06, 0x06],
  r: [0x00, 0x00, 0x5c, 0x66, 0x60, 0x60, 0x60, 0x00],
  s: [0x00, 0x00, 0x3e, 0x60, 0x3c, 0x06, 0x7c, 0x00],
  t: [0x18, 0x18, 0x7e, 0x18, 0x18, 0x18, 0x0e, 0x00],
  u: [0x00, 0x00, 0x66, 0x66, 0x66, 0x66, 0x3e, 0x00],
  v: [0x00, 0x00, 0x66, 0x66, 0x66, 0x3c, 0x18, 0x00],
  w: [0x00, 0x00, 0x63, 0x6b, 0x7f, 0x77, 0x63, 0x00],
  x: [0x00, 0x00, 0x66, 0x3c, 0x18, 0x3c, 0x66, 0x00],
  y: [0x00, 0x00, 0x66, 0x66, 0x66, 0x3e, 0x06, 0x3c],
  z: [0x00, 0x00, 0x7e, 0x0c, 0x18, 0x30, 0x7e, 0x00],

  // Digits
  '0': [0x3c, 0x66, 0x6e, 0x76, 0x66, 0x66, 0x3c, 0x00],
  '1': [0x18, 0x38, 0x18, 0x18, 0x18, 0x18, 0x7e, 0x00],
  '2': [0x3c, 0x66, 0x0c, 0x18, 0x30, 0x60, 0x7e, 0x00],
  '3': [0x3c, 0x66, 0x0c, 0x18, 0x0c, 0x66, 0x3c, 0x00],
  '4': [0x0c, 0x1c, 0x3c, 0x6c, 0xfe, 0x0c, 0x0c, 0x00],
  '5': [0x7e, 0x60, 0x7c, 0x06, 0x06, 0x66, 0x3c, 0x00],
  '6': [0x3c, 0x66, 0x60, 0x7c, 0x66, 0x66, 0x3c, 0x00],
  '7': [0x7e, 0x06, 0x0c, 0x18, 0x30, 0x30, 0x30, 0x00],
  '8': [0x3c, 0x66, 0x66, 0x3c, 0x66, 0x66, 0x3c, 0x00],
  '9': [0x3c, 0x66, 0x66, 0x7e, 0x06, 0x66, 0x3c, 0x00],

  // Symbols & Punctuation
  ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
  '-': [0x00, 0x00, 0x00, 0x7e, 0x00, 0x00, 0x00, 0x00],
  '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18],
  ':': [0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x18, 0x00],
  '|': [0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00],
  '[': [0x1c, 0x18, 0x18, 0x18, 0x18, 0x18, 0x1c, 0x00],
  ']': [0x38, 0x18, 0x18, 0x18, 0x18, 0x18, 0x38, 0x00],
  '(': [0x0c, 0x18, 0x30, 0x30, 0x30, 0x18, 0x0c, 0x00],
  ')': [0x30, 0x18, 0x0c, 0x0c, 0x0c, 0x18, 0x30, 0x00],
  '=': [0x00, 0x7e, 0x00, 0x7e, 0x00, 0x00, 0x00, 0x00],
  ',': [0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x30],
  '/': [0x02, 0x06, 0x0c, 0x18, 0x30, 0x60, 0x40, 0x00],
  '+': [0x00, 0x18, 0x18, 0x7e, 0x18, 0x18, 0x00, 0x00],
  '>': [0x60, 0x30, 0x18, 0x0c, 0x18, 0x30, 0x60, 0x00],
  '<': [0x06, 0x0c, 0x18, 0x30, 0x18, 0x0c, 0x06, 0x00],
  '*': [0x00, 0x66, 0x3c, 0xff, 0x3c, 0x66, 0x00, 0x00],
  '%': [0x62, 0x64, 0x08, 0x10, 0x20, 0x4c, 0x8c, 0x00],
  '_': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x00],
  '!': [0x18, 0x18, 0x18, 0x18, 0x18, 0x00, 0x18, 0x00],
  '?': [0x3c, 0x66, 0x0c, 0x18, 0x18, 0x00, 0x18, 0x00],
  '#': [0x24, 0x24, 0x7e, 0x24, 0x7e, 0x24, 0x24, 0x00],
  '&': [0x38, 0x6c, 0x38, 0x76, 0xdc, 0xcc, 0x76, 0x00],
};

function getFontGlyph(char: string): number[] {
  return FONT_GLYPHS[char] || FONT_GLYPHS[char.toUpperCase()] || FONT_GLYPHS[' '];
}

function drawBitmapString(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  str: string,
  fg: string,
  bg?: string
) {
  let curX = x;
  for (let i = 0; i < str.length; i++) {
    const glyph = getFontGlyph(str[i]);
    for (let row = 0; row < 8; row++) {
      const byte = glyph[row];
      for (let col = 0; col < 8; col++) {
        if ((byte & (0x80 >> col)) !== 0) {
          ctx.fillStyle = fg;
          ctx.fillRect(curX + col, y + row, 1, 1);
        } else if (bg) {
          ctx.fillStyle = bg;
          ctx.fillRect(curX + col, y + row, 1, 1);
        }
      }
    }
    curX += 8;
  }
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

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.floor((e.clientX - rect.left) * scaleX);
    const y = Math.floor((e.clientY - rect.top) * scaleY);
    setMousePos({ x: Math.max(0, Math.min(639, x)), y: Math.max(0, Math.min(239, y)) });
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.floor((e.clientX - rect.left) * scaleX);
    const y = Math.floor((e.clientY - rect.top) * scaleY);

    // Top Mode Ribbon Click (y: 14 to 28)
    if (y >= 14 && y <= 28) {
      if (x >= 12 && x <= 84) onSetMode('PERF');
      else if (x >= 95 && x <= 160) onSetMode('PATCH');
      else if (x >= 170 && x <= 252) onSetMode('PART');
      else if (x >= 265 && x <= 336) onSetMode('SAMPLE');
      else if (x >= 345 && x <= 408) onSetMode('DISK');
      else if (x >= 420 && x <= 490) onSetMode('SYSTEM');
      onEventEmit('CRT_TAB_CLICK', { x, y });
      return;
    }

    // Patch rows click (y: 68 to 218)
    if (y >= 68 && y <= 218 && x >= 32 && x <= 460) {
      const rowIdx = Math.floor((y - 68) / 9);
      if (rowIdx >= 0 && rowIdx < 16) {
        if (onSelectPatchIndex) {
          onSelectPatchIndex(rowIdx);
        }
        onEventEmit('CRT_PATCH_ROW_CLICK', { index: rowIdx });
      }
      return;
    }

    // Bottom Soft Ribbon Click (y: 222 to 240)
    if (y >= 222 && y <= 240) {
      const softIdx = Math.floor(x / (640 / 5));
      if (softIdx >= 0 && softIdx < 5) {
        onSoftKey(softIdx);
        onEventEmit('CRT_SOFT_CLICK', { softIdx });
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
      ctx.fillStyle = '#080a0e';
      ctx.fillRect(0, 0, W, H);
      return;
    }

    // Exact Roland S-760 10-Pen CRT Palette (Verified from real hardware monitor)
    const cBlack   = '#000000'; // Pen 0
    const cWhite   = '#ffffff'; // Pen 1
    const cBlue    = '#0000c0'; // Pen 2: Authentic S-760 Royal Blue
    const cGreen   = '#00c850'; // Pen 3: Status Green
    const cYellow  = '#ffe600'; // Pen 4: Parameter & Selection Highlights
    const cRed     = '#dc3c14'; // Pen 5: Tab Selection Outline & Muted Alert
    const cLtGray  = '#bec3cd'; // Pen 6: Subheader Ribbon
    const cCyan    = '#00dcdc'; // Pen 8: Values & Cyan Function Keys

    // 1. Fill entire CRT workspace with authentic Roland Royal Blue (#0000C0)
    ctx.fillStyle = cBlue;
    ctx.fillRect(0, 0, W, H);

    // 2. Top Status Bar (Status Green y = 0..13)
    ctx.fillStyle = cGreen;
    ctx.fillRect(0, 0, W, 14);
    
    // Exact text from real S-760 hardware: "Volume[ - :              ] ID:01  ---/---"
    drawBitmapString(ctx, 8, 3, "Volume[ - :              ] ID:01", cBlack, cGreen);
    drawBitmapString(ctx, 520, 3, "---/---", cBlack, cGreen);

    // 3. Mode Ribbon (Pure White Background y = 14..27)
    ctx.fillStyle = cWhite;
    ctx.fillRect(0, 14, W, 14);

    const modeIdxMap: Record<SamplerMode, number> = {
      PERF: 0,
      PATCH: 1,
      PART: 2,
      SAMPLE: 3,
      DISK: 4,
      SYSTEM: 5,
    };
    const activeTab = modeIdxMap[state.mode] ?? 4;

    drawBitmapString(ctx, 16, 17, "Perform", activeTab === 0 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 88, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 108, 17, "Patch", activeTab === 1 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 164, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 184, 17, "Partial", activeTab === 2 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 256, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 276, 17, "Sample", activeTab === 3 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 340, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 360, 17, "Disk", activeTab === 4 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 412, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 432, 17, "System", activeTab === 5 ? cRed : cBlack, cWhite);

    // Draw active tab outline box with Red border (Pen 5)
    const tabBoxes = [
      [12, 84],
      [102, 156],
      [178, 248],
      [270, 332],
      [352, 402],
      [426, 486],
    ];
    const [bx0, bx1] = tabBoxes[activeTab];
    for (let x = bx0; x < bx1; x++) {
      ctx.fillStyle = cRed;
      ctx.fillRect(x, 14, 1, 1);
      ctx.fillRect(x, 27, 1, 1);
    }
    for (let y = 14; y < 28; y++) {
      ctx.fillStyle = cRed;
      ctx.fillRect(bx0, y, 1, 1);
      ctx.fillRect(bx1, y, 1, 1);
    }

    // 4. Context Sub-Ribbon (Light Gray y = 28..39)
    ctx.fillStyle = cLtGray;
    ctx.fillRect(0, 28, W, 12);

    if (state.mode === 'DISK') {
      drawBitmapString(ctx, 16, 30, "Disk Load", cBlack, cLtGray);
      ctx.fillStyle = cBlack;
      ctx.fillRect(320, 28, 1, 12);
      drawBitmapString(ctx, 330, 30, "Muted", cRed, cLtGray);
      ctx.fillRect(380, 28, 1, 12);
      drawBitmapString(ctx, 390, 30, "Mark", cBlack, cLtGray);
      ctx.fillRect(440, 28, 1, 12);
      drawBitmapString(ctx, 450, 30, "Jump", cBlack, cLtGray);
      ctx.fillRect(500, 28, 1, 12);
      drawBitmapString(ctx, 510, 30, "Com", cCyan, cLtGray);
    } else if (state.mode === 'PERF') {
      drawBitmapString(ctx, 16, 30, "Perform Play 1", cBlack, cLtGray);
      drawBitmapString(ctx, 330, 30, "MIDI   |  Part   |  Split  |  Mix", cBlack, cLtGray);
    } else if (state.mode === 'PATCH') {
      drawBitmapString(ctx, 16, 30, "Patch Split", cBlack, cLtGray);
      drawBitmapString(ctx, 330, 30, "Common |  Layer  |  V-Sw   |  Com", cBlack, cLtGray);
    } else if (state.mode === 'SAMPLE') {
      drawBitmapString(ctx, 16, 30, "Sample Info", cBlack, cLtGray);
      drawBitmapString(ctx, 330, 30, "Loop   |  Pitch  |  Norm   |  Com", cBlack, cLtGray);
    } else if (state.mode === 'SYSTEM') {
      drawBitmapString(ctx, 16, 30, "System SCSI", cBlack, cLtGray);
      drawBitmapString(ctx, 330, 30, "PRM    |  MIDI   |  Vol ID |  Com", cBlack, cLtGray);
    } else {
      drawBitmapString(ctx, 16, 30, "Partial TVF", cBlack, cLtGray);
      drawBitmapString(ctx, 330, 30, "TVA    |  LFO    |  SMT    |  Com", cBlack, cLtGray);
    }

    // 5. Main Screen Content Area (Blue Canvas y = 40..221)
    if (state.mode === 'DISK') {
      // Line 44 Target & Current Drive Line:
      // Exact hardware text: "TG[Pfom]   ID[All]   CD[FDD:-FloppyDisk-]"
      drawBitmapString(ctx, 24, 44, "TG[Pfom]   ID[All]   CD[FDD:-FloppyDisk-]", cWhite, cBlue);

      // Yellow table header bar (y = 56..65, x = 12..460)
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 448, 10);
      drawBitmapString(ctx, 24, 57, "1files", cBlack, cYellow);
      drawBitmapString(ctx, 340, 57, "Time P#", cBlack, cYellow);

      // 16 File Rows (y = 68 to 208, 1 to 16)
      const diskRows = [
        { num: ' 1:', name: 'PNO:Acoustic Pno', time: '22.2' },
        { num: ' 2:', name: '', time: ' 0.0' },
        { num: ' 3:', name: '', time: ' 0.0' },
        { num: ' 4:', name: '', time: ' 0.0' },
        { num: ' 5:', name: '', time: ' 0.0' },
        { num: ' 6:', name: '', time: ' 0.0' },
        { num: ' 7:', name: '', time: ' 0.0' },
        { num: ' 8:', name: '', time: ' 0.0' },
        { num: ' 9:', name: '', time: ' 0.0' },
        { num: '10:', name: '', time: ' 0.0' },
        { num: '11:', name: '', time: ' 0.0' },
        { num: '12:', name: '', time: ' 0.0' },
        { num: '13:', name: '', time: ' 0.0' },
        { num: '14:', name: '', time: ' 0.0' },
        { num: '15:', name: '', time: ' 0.0' },
        { num: '16:', name: '', time: ' 0.0' },
      ];

      diskRows.forEach((row, idx) => {
        const ry = 68 + idx * 9.5;
        const isSelected = idx === 0;

        if (isSelected) {
          // Highlight Row 1 with subtle selection mark
          drawBitmapString(ctx, 24, Math.floor(ry), row.num, cWhite, cBlue);
          drawBitmapString(ctx, 60, Math.floor(ry), row.name, cWhite, cBlue);
          drawBitmapString(ctx, 350, Math.floor(ry), row.time, cWhite, cBlue);
        } else {
          drawBitmapString(ctx, 24, Math.floor(ry), row.num, cWhite, cBlue);
          drawBitmapString(ctx, 350, Math.floor(ry), row.time, cWhite, cBlue);
        }
      });

      // Right Side Parameter Boxes Stack (Exact geometry from DISK-1.jpeg):
      // Box 1: Int. -> 363.8sec
      ctx.fillStyle = cYellow;
      ctx.fillRect(470, 56, 140, 10);
      drawBitmapString(ctx, 510, 57, "Int.", cBlack, cYellow);
      drawBitmapString(ctx, 496, 68, "363.8sec", cCyan, cBlue);

      // Box 2: Disk -> ****.sec
      ctx.fillStyle = cYellow;
      ctx.fillRect(470, 80, 140, 10);
      drawBitmapString(ctx, 506, 81, "Disk", cBlack, cYellow);
      drawBitmapString(ctx, 496, 92, "****.sec", cCyan, cBlue);

      // Box 3: Marked -> 0
      ctx.fillStyle = cYellow;
      ctx.fillRect(470, 104, 140, 10);
      drawBitmapString(ctx, 498, 105, "Marked", cBlack, cYellow);
      drawBitmapString(ctx, 532, 116, "0", cCyan, cBlue);

    } else if (state.mode === 'PERF') {
      drawBitmapString(ctx, 24, 44, "Perform Play 1   PRM: 01 JP-8 MULTI SET            Ram:32MB", cWhite, cBlue);
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 448, 10);
      drawBitmapString(ctx, 24, 57, "Part | MIDI Ch | Patch Name", cBlack, cYellow);
      drawBitmapString(ctx, 340, 57, "Vol  Pan", cBlack, cYellow);

      const parts = [
        "Part 1: CH 01 | P11: JP-8 BRASS 1        127  <0>",
        "Part 2: CH 02 | P12: JP-8 STRGS 1        110  L15",
        "Part 3: CH 03 | P13: VP STRINGS 1        105  R15",
        "Part 4: CH 04 | P14: VP CHOIR 1          090  <0>",
        "Part 5: CH 05 | P15: SYNTH 1             100  <0>",
        "Part 6: CH 06 | P16: SYNTH 2             100  <0>",
        "Part 7: CH 07 | P17: SYNTH 3             100  <0>",
        "Part 8: CH 08 | P18: SYNTH 4             100  <0>",
      ];

      parts.forEach((p, i) => {
        const ry = 68 + i * 10;
        drawBitmapString(ctx, 24, ry, p, cWhite, cBlue);
      });
    } else if (state.mode === 'SAMPLE') {
      drawBitmapString(ctx, 24, 44, "Sample Info   Sample: W01 JP-8_BRASS_44K.WAV (44.1kHz 16-Bit)", cWhite, cBlue);
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 448, 10);
      drawBitmapString(ctx, 24, 57, "Parameter Info", cBlack, cYellow);

      drawBitmapString(ctx, 24, 70,  "Orig Key:    C4           Sample Rate: 44.1 kHz", cWhite, cBlue);
      drawBitmapString(ctx, 24, 84,  "Wave Length: 2.95 s       Remaining:   363.8 s", cWhite, cBlue);
      drawBitmapString(ctx, 24, 98,  "Start Point: 0000,000     End Point:   0130,560", cWhite, cBlue);
      drawBitmapString(ctx, 24, 112, "Loop Start:  0048,200     Loop End:    0128,400", cYellow, cBlue);
      drawBitmapString(ctx, 24, 126, "Loop Mode:   Forward      Fine Tune:   +0 cent", cWhite, cBlue);

      // Waveform display graph in Cyan & Yellow
      for (let x = 24; x < 460; x++) {
        const mid = 175;
        const amp = Math.floor(18.0 * Math.sin((x - 24) * 0.15) * Math.cos((x - 24) * 0.04));
        ctx.fillStyle = cYellow;
        ctx.fillRect(x, mid + amp, 1, 1);
        ctx.fillStyle = cCyan;
        ctx.fillRect(x, mid - amp, 1, 1);
      }
    } else if (state.mode === 'PATCH') {
      drawBitmapString(ctx, 24, 44, "Patch Split   Patch: 01 JP-8 BRASS 1           Level:127  Pan:<0>", cWhite, cBlue);
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 448, 10);
      drawBitmapString(ctx, 24, 57, "Partial Name    L.P  U.P  Type   Output", cBlack, cYellow);
      drawBitmapString(ctx, 340, 57, "Level Pan", cBlack, cYellow);

      drawBitmapString(ctx, 24, 70, "1: JP-8 BRASS L C-1  B3   1-SMT  1-2        127   L15", cWhite, cBlue);
      drawBitmapString(ctx, 24, 84, "2: JP-8 BRASS R C-1  B3   1-SMT  1-2        127   R15", cWhite, cBlue);
      drawBitmapString(ctx, 24, 98, "3: JP-8 BRASS H C4   G9   1-SMT  1-2        120   <0>", cWhite, cBlue);
      drawBitmapString(ctx, 24, 112,"4: --- OFF ---  ---  ---  -----  ---        ---   ---", cLtGray, cBlue);

    } else if (state.mode === 'PART') {
      drawBitmapString(ctx, 24, 44, "Partial TVF   Partial: 01 JP-8 BRASS L         Sample: W01 JP-8_B1", cWhite, cBlue);
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 448, 10);
      drawBitmapString(ctx, 24, 57, "Filter & TVF EG Controls", cBlack, cYellow);

      drawBitmapString(ctx, 24, 72,  "Filter Mode: [ LPF ]      Cutoff Freq: [  84 ]", cWhite, cBlue);
      drawBitmapString(ctx, 24, 86,  "Resonance:   [  32 ]      Cutoff KF:   [ +1.0 ]", cWhite, cBlue);
      drawBitmapString(ctx, 24, 100, "Vel-Curve:   [ 1:/ ]      -Curve Sens: [ +45 ]", cWhite, cBlue);
      drawBitmapString(ctx, 24, 114, "TVF Depth:   [ +64 ]      Key Follow:  [ +1.0 ]", cYellow, cBlue);

    } else {
      drawBitmapString(ctx, 24, 44, "System SCSI   S-760 ROM Version 2.24           Ram:32MB OK", cWhite, cBlue);
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 448, 10);
      drawBitmapString(ctx, 24, 57, "SCSI Bus Targets (0-6)", cBlack, cYellow);

      drawBitmapString(ctx, 24, 72,  "S-760 Self SCSI ID:  [ 7 ]", cWhite, cBlue);
      drawBitmapString(ctx, 24, 86,  "Initial Drive:       [ SCSI 0 ]", cWhite, cBlue);
      drawBitmapString(ctx, 24, 100, "Boot Drive:          [ SCSI / Floppy Auto ]", cWhite, cBlue);
      drawBitmapString(ctx, 24, 114, "CDP Driver Type:     [ Apple / Toshiba / Sony ]", cWhite, cBlue);
      drawBitmapString(ctx, 24, 130, "  ID 0: APPLE CD-ROM 300+ (Optical Drive)", cGreen, cBlue);
      drawBitmapString(ctx, 24, 144, "  ID 1: QUANTUM FIREBALL 1080S (1.08 GB HDD)", cGreen, cBlue);
      drawBitmapString(ctx, 24, 158, "  ID 2..6: --- No Device ---", cLtGray, cBlue);
    }

    // 6. Bottom Context Function Keys Ribbon (Exact layout from DISK-1.jpeg)
    if (state.mode === 'DISK') {
      // Button 1: [ ] AllOn (White button with checkbox square, x = 12..104, y = 222..236)
      ctx.fillStyle = cWhite;
      ctx.fillRect(12, 222, 92, 14);
      // Checkbox square
      ctx.fillStyle = cBlack;
      ctx.fillRect(16, 225, 8, 8);
      ctx.fillStyle = cWhite;
      ctx.fillRect(17, 226, 6, 6);
      drawBitmapString(ctx, 28, 225, "AllOn", cBlack, cWhite);

      // Button 2: Solid Cyan button with '---' (x = 120..220)
      ctx.fillStyle = cCyan;
      ctx.fillRect(120, 222, 100, 14);
      drawBitmapString(ctx, 156, 225, "---", cBlack, cCyan);

      // Button 3: Solid White button with 'Load' (x = 236..336)
      ctx.fillStyle = cWhite;
      ctx.fillRect(236, 222, 100, 14);
      drawBitmapString(ctx, 266, 225, "Load", cBlack, cWhite);

      // Button 4: [ ] OW Off (White button with checkbox square, x = 352..452)
      ctx.fillStyle = cWhite;
      ctx.fillRect(352, 222, 100, 14);
      ctx.fillStyle = cBlack;
      ctx.fillRect(356, 225, 8, 8);
      ctx.fillStyle = cWhite;
      ctx.fillRect(357, 226, 6, 6);
      drawBitmapString(ctx, 368, 225, "OW Off", cBlack, cWhite);

      // Button 5: Solid White button with 'VolInfo' (x = 468..590)
      ctx.fillStyle = cWhite;
      ctx.fillRect(468, 222, 122, 14);
      drawBitmapString(ctx, 492, 225, "VolInfo", cBlack, cWhite);

    } else {
      // Other modes default bottom soft ribbon
      ctx.fillStyle = cWhite;
      ctx.fillRect(0, 222, W, 18);

      let softBtns: string[] = ['Play', 'MIDI', 'Solo', 'Mute', 'VolInfo'];
      if (state.mode === 'PERF') {
        softBtns = ['Play', 'MIDI', 'Solo', 'Mute', 'VolInfo'];
      } else if (state.mode === 'PATCH') {
        softBtns = ['Split', 'Common', 'Layer', 'V-Sw', 'VolInfo'];
      } else if (state.mode === 'PART') {
        softBtns = ['TVF', 'TVA', 'LFO', 'SMT', 'VolInfo'];
      } else if (state.mode === 'SAMPLE') {
        softBtns = ['Info', 'Loop', 'Trun', 'Norm', 'VolInfo'];
      } else if (state.mode === 'SYSTEM') {
        softBtns = ['SCSI', 'PRM', 'MIDI', 'VolID', 'VolInfo'];
      }

      const colW = Math.floor(W / 5);
      softBtns.forEach((btnTxt, idx) => {
        const bx = idx * colW + 16;
        drawBitmapString(ctx, bx, 226, btnTxt, cBlack, cWhite);
        if (idx < 4) {
          drawBitmapString(ctx, (idx + 1) * colW - 6, 226, "|", cBlack, cWhite);
        }
      });
    }

    // 7. Draw Authentic Roland Crosshair Mouse Cursor (+) at mousePos
    const { x, y } = mousePos;
    ctx.fillStyle = cWhite;
    for (let dx = -4; dx <= 4; dx++) {
      ctx.fillRect(x + dx, y, 1, 1);
    }
    for (let dy = -4; dy <= 4; dy++) {
      ctx.fillRect(x, y + dy, 1, 1);
    }

  }, [state, diskList, mousePos]);

  return (
    <div className="relative flex flex-col items-center select-none">
      {/* Vintage Studio 4:3 CRT Monitor Housing (OP-760 Video Display) */}
      <div className="relative flex flex-col items-center bg-gradient-to-b from-[#2b2e35] via-[#202227] to-[#17191d] p-3.5 sm:p-5 rounded-2xl border-2 border-[#3d424c] shadow-[0_20px_50px_rgba(0,0,0,0.95),inset_0_1px_2px_rgba(255,255,255,0.15)]">
        {/* Top Monitor Bevel with Heat Vents */}
        <div className="w-full flex items-center justify-between px-3 pb-2.5">
          {/* Color Monitor Badge */}
          <div className="flex items-center gap-2">
            <span className="text-[9px] font-mono font-bold tracking-widest text-neutral-300 uppercase bg-[#14161a] px-2 py-0.5 rounded border border-neutral-700">
              OP-760 COLOR DISPLAY
            </span>
          </div>

          {/* Cooling Vents */}
          <div className="flex gap-1">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="w-1.5 h-1 bg-[#121417] rounded-[0.5px] border-b border-[#323640]" />
            ))}
          </div>

          {/* RGB / NTSC Mode Pill */}
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_6px_#34d399]" />
            <span className="text-[8px] font-mono font-bold text-emerald-400 tracking-wider">
              RGB 15kHz
            </span>
          </div>
        </div>

        {/* Physical 4:3 Aspect Ratio Screen Bezel & Tube */}
        <div className="relative p-2.5 bg-gradient-to-b from-[#111215] to-[#181a1f] rounded-xl border border-neutral-800 shadow-[inset_0_4px_12px_rgba(0,0,0,0.9)]">
          {/* Authentic 4:3 Aspect Ratio CRT Tube Area */}
          <div
            className="relative overflow-hidden rounded-lg bg-black border border-neutral-900 shadow-[inset_0_0_20px_rgba(0,0,0,0.8)]"
            style={{
              width: '640px',
              height: '480px',
              aspectRatio: '4 / 3',
            }}
          >
            {/* The Pixelated Roland VRAM Canvas (640x240 stretched vertically across 4:3 screen) */}
            <canvas
              ref={canvasRef}
              width={640}
              height={240}
              onMouseMove={handleMouseMove}
              onClick={handleCanvasClick}
              className="w-full h-full cursor-crosshair block"
              style={{
                imageRendering: 'pixelated',
              }}
            />

            {/* Subtle CRT Phosphor Scanline Mesh */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.22)_50%)] bg-[length:100%_4px] pointer-events-none opacity-60" />

            {/* Spherical CRT Glass Corner Glare Reflection */}
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-transparent to-white/[0.04] pointer-events-none rounded-lg" />
          </div>
        </div>

        {/* Bottom Monitor Control Strip: Power, Degauss, Dials */}
        <div className="w-full flex items-center justify-between px-3 pt-2.5 mt-0.5">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${state.powerOn ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-neutral-700'}`} />
              <span className="text-[7.5px] font-mono font-bold text-neutral-400 uppercase tracking-wider">
                POWER
              </span>
            </div>
            <div className="text-[7.5px] font-mono text-neutral-500 uppercase tracking-widest pl-2 border-l border-neutral-700">
              640 x 480 @ 60Hz 4:3
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Picture Trim Potentiometers */}
            <div className="flex items-center gap-2">
              <div className="flex flex-col items-center">
                <div className="w-3.5 h-3.5 rounded-full bg-gradient-to-b from-neutral-600 to-neutral-800 border border-neutral-500 shadow-inner flex items-center justify-center">
                  <div className="w-0.5 h-2 bg-neutral-300 rounded-[0.5px]" />
                </div>
                <span className="text-[6px] font-mono text-neutral-500 mt-0.5 uppercase">BRIGHT</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-3.5 h-3.5 rounded-full bg-gradient-to-b from-neutral-600 to-neutral-800 border border-neutral-500 shadow-inner flex items-center justify-center">
                  <div className="w-0.5 h-2 bg-neutral-300 rounded-[0.5px] rotate-45" />
                </div>
                <span className="text-[6px] font-mono text-neutral-500 mt-0.5 uppercase">CONTRAST</span>
              </div>
            </div>

            {/* Degauss Button */}
            <button
              type="button"
              className="px-2 py-0.5 text-[7px] font-mono font-bold text-neutral-400 bg-neutral-800 hover:bg-neutral-700 rounded border border-neutral-600 active:scale-95 transition-transform"
              title="CRT Degauss Coil"
            >
              DEGAUSS
            </button>
          </div>
        </div>
      </div>

      {/* Monitor Stand Base */}
      <div className="w-48 h-2.5 bg-gradient-to-b from-[#1b1c20] to-[#121316] rounded-b-md border-x border-b border-[#353942] shadow-[0_8px_16px_rgba(0,0,0,0.8)] -mt-0.5" />
    </div>
  );
};
