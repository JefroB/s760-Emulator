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

// Exact 8x8 Roland OP-760 ROM Bitmap Font Glyphs from S-760 VDP firmware
const FONT_GLYPHS: Record<string, number[]> = {
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
  v: [0x00, 0x00, 0x66, 0x66, 0x66, 0x3c, 0x18, 0x00],
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
};

function getFontGlyph(char: string): number[] {
  const upper = char.toUpperCase();
  if (char === 'v') return FONT_GLYPHS.v;
  return FONT_GLYPHS[upper] || FONT_GLYPHS[char] || FONT_GLYPHS[' '];
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

    // Top Menu Ribbon Click (y: 14 to 28)
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

    // Patch rows click (y: 58 to 218)
    if (y >= 58 && y <= 218 && x >= 14 && x <= 480) {
      const rowIdx = Math.floor((y - 58) / 10);
      if (onSelectPatchIndex) {
        onSelectPatchIndex(rowIdx);
      }
      onEventEmit('CRT_PATCH_ROW_CLICK', { index: rowIdx });
      return;
    }

    // Bottom Soft Ribbon Click (y: 222 to 240)
    if (y >= 222 && y <= 240) {
      const softIdx = Math.floor((x - 10) / 150);
      if (softIdx >= 0 && softIdx < 4) {
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

    // Exact Roland S-760 10-Pen CRT Palette
    const cBlack   = '#000000'; // Pen 0
    const cWhite   = '#ffffff'; // Pen 1
    const cBlue    = '#0000c0'; // Pen 2: Authentic S-760 Royal Blue
    const cGreen   = '#00c850'; // Pen 3: Status Green
    const cYellow  = '#ffe600'; // Pen 4: Parameter & Value Highlights
    const cRed     = '#dc3c14'; // Pen 5: Tab Selection Highlight
    const cLtGray  = '#bec3cd'; // Pen 6: Light Gray Header Ribbon
    const cCyan    = '#00dcdc'; // Pen 8: Cyan Waveform Graphics

    // 1. Fill CRT workspace with authentic Roland Royal Blue (#0000C0)
    ctx.fillStyle = cBlue;
    ctx.fillRect(0, 0, W, H);

    // 2. Top Status Bar (Status Green y = 0..13)
    ctx.fillStyle = cGreen;
    ctx.fillRect(0, 0, W, 14);
    drawBitmapString(ctx, 6, 3, "VOLUME[ - :      ]                 ID:04              ---/---", cBlack, cGreen);

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

    drawBitmapString(ctx, 16, 17, "PERFORM", activeTab === 0 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 88, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 108, 17, "PATCH", activeTab === 1 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 164, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 184, 17, "PARTIAL", activeTab === 2 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 256, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 276, 17, "SAMPLE", activeTab === 3 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 340, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 360, 17, "DISK", activeTab === 4 ? cRed : cBlack, cWhite);
    drawBitmapString(ctx, 412, 17, "|", cBlack, cWhite);
    drawBitmapString(ctx, 432, 17, "SYSTEM", activeTab === 5 ? cRed : cBlack, cWhite);

    // Draw active tab box with Red border (Pen 5)
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
      drawBitmapString(ctx, 8, 30, "CONVERT LD[S]        |  MUTED  |  MARK  |  JUMP  |  COM", cBlack, cLtGray);
    } else if (state.mode === 'PERF') {
      drawBitmapString(ctx, 8, 30, "PLAY [PERFORM]       |  MIDI  |  PART  |  SPLIT |  MIX", cBlack, cLtGray);
    } else if (state.mode === 'PATCH') {
      drawBitmapString(ctx, 8, 30, "EDIT [PATCH]         |  SPLIT |  LAYER |  V-SW  |  COMMON", cBlack, cLtGray);
    } else if (state.mode === 'SAMPLE') {
      drawBitmapString(ctx, 8, 30, "EDIT [SAMPLE]        |  LOOP  |  PITCH |  NORM  |  CONVERT", cBlack, cLtGray);
    } else if (state.mode === 'SYSTEM') {
      drawBitmapString(ctx, 8, 30, "SETUP [SYSTEM]       |  MIDI   |  TEST  |  FORMAT|  SAVESYS", cBlack, cLtGray);
    } else {
      drawBitmapString(ctx, 8, 30, "EDIT [PARTIAL]       |  TVF   |  TVA   |  ENV   |  LFO", cBlack, cLtGray);
    }

    // 5. Main Screen Content Area (Blue Canvas y = 40..221)
    if (state.mode === 'DISK') {
      drawBitmapString(ctx, 16, 44, "[LOAD:SOUND]  TARGET: FLOPPY DISK (FD)       CD[RAM: 32MB]", cWhite, cBlue);

      // White line under subheader
      for (let x = 16; x < 624; x++) {
        ctx.fillStyle = cWhite;
        ctx.fillRect(x, 54, 1, 1);
      }

      // Exact Roland Sound Disk Patch rows
      const diskPatches = [
        'LJUA1A75-80A',
        '75CQNAAAAAAA',
        '75A1AAAAAAAA',
        '75A2AAAAAAAA',
        '75A3AAAAAAAA',
        '75A4AAAAAAAA',
        '75A5AAAAAAAA',
        '80CQNAAAAAAA',
        '80A1AAAAAAAA',
        '80A4AAAAAAAA',
        '80A3AAAAAAAA',
        '80A2AAAAAAAA',
        'QJUDIFE75-80',
        'LJUA1A81-82A',
        '81CQNAAAAAAA',
        '81A1AAAAAAAA',
      ];

      diskPatches.forEach((name, i) => {
        const rowY = 60 + i * 10;
        const numStr = (i + 1).toString().padStart(2, '0');
        const rowTxt = `P${numStr}: ${name}`;

        if (i === (state.currentPatchIndex % 16)) {
          // Highlight Selected Row in Yellow
          for (let py = rowY - 1; py < rowY + 9; py++) {
            for (let px = 14; px < 174; px++) {
              ctx.fillStyle = cYellow;
              ctx.fillRect(px, py, 1, 1);
            }
          }
          drawBitmapString(ctx, 16, rowY, rowTxt, cBlack, cYellow);
        } else {
          drawBitmapString(ctx, 16, rowY, rowTxt, cWhite, cBlue);
        }
      });

      // Right Parameter Boxes (Yellow filled boxes with black text)
      const drawParamBox = (pbx: number, pby: number, pbw: number, pbh: number, txt: string) => {
        for (let py = pby; py < pby + pbh; py++) {
          for (let px = pbx; px < pbx + pbw; px++) {
            ctx.fillStyle = cYellow;
            ctx.fillRect(px, py, 1, 1);
          }
        }
        drawBitmapString(ctx, pbx + 6, pby + 2, txt, cBlack, cYellow);
      };

      drawParamBox(500, 58, 120, 12, "   INT.");
      drawParamBox(500, 74, 120, 12, " 2954SEC");
      drawParamBox(500, 90, 120, 12, "  MARKED");
      drawParamBox(500, 106, 120, 12, "    0");
      drawParamBox(500, 122, 120, 12, "   +/-");

    } else if (state.mode === 'PERF') {
      drawBitmapString(ctx, 16, 44, "[PERFORM PLAY]  PRM: 01 JP-8 MULTI SET       CD[RAM: 32MB]", cWhite, cBlue);
      for (let x = 16; x < 624; x++) {
        ctx.fillStyle = cWhite;
        ctx.fillRect(x, 54, 1, 1);
      }

      const parts = [
        "PART 1: CH 01 | P11: JP-8 BRASS 1   | VOL: 127 | PAN: <0> | OUT: 1-2",
        "PART 2: CH 02 | P12: JP-8 STRGS 1   | VOL: 110 | PAN: L15 | OUT: 1-2",
        "PART 3: CH 03 | P13: VP STRINGS 1   | VOL: 105 | PAN: R15 | OUT: 1-2",
        "PART 4: CH 04 | P14: VP CHOIR 1     | VOL: 090 | PAN: <0> | OUT: 3-4",
        "PART 5: CH 05 | P15: SYNTH 1        | VOL: 100 | PAN: <0> | OUT: 1-2",
        "PART 6: CH 06 | P16: SYNTH 2        | VOL: 100 | PAN: <0> | OUT: 1-2",
        "PART 7: CH 07 | P17: SYNTH 3        | VOL: 100 | PAN: <0> | OUT: 1-2",
        "PART 8: CH 08 | P18: SYNTH 4        | VOL: 100 | PAN: <0> | OUT: 1-2",
      ];

      parts.forEach((p, i) => {
        const rowY = 60 + i * 10;
        if (i === 0) {
          for (let py = rowY - 1; py < rowY + 9; py++) {
            for (let px = 14; px < 570; px++) {
              ctx.fillStyle = cYellow;
              ctx.fillRect(px, py, 1, 1);
            }
          }
          drawBitmapString(ctx, 16, rowY, p, cBlack, cYellow);
        } else {
          drawBitmapString(ctx, 16, rowY, p, cWhite, cBlue);
        }
      });
    } else if (state.mode === 'SAMPLE') {
      drawBitmapString(ctx, 16, 44, "[SAMPLE WAVE]  W01: JP-8_BRASS_44K.WAV   (16-BIT MONO 44.1KHZ)", cWhite, cBlue);
      for (let x = 16; x < 624; x++) {
        ctx.fillStyle = cWhite;
        ctx.fillRect(x, 54, 1, 1);
      }

      drawBitmapString(ctx, 20, 64,  "SAMPLE LENGTH: 130,560 WORDS (2.95 SEC)  ORIGINAL KEY: C4", cWhite, cBlue);
      drawBitmapString(ctx, 20, 78,  "LOOP MODE:     FORWARD                   FINE TUNE:    +0", cWhite, cBlue);
      drawBitmapString(ctx, 20, 92,  "START POINT:   0000,000                  END POINT:    0130,560", cWhite, cBlue);
      drawBitmapString(ctx, 20, 106, "LOOP START:    0048,200                  LOOP END:     0128,400", cYellow, cBlue);

      // Waveform display graph
      for (let x = 20; x < 480; x++) {
        const mid = 150;
        const amp = Math.floor(15.0 * Math.sin((x - 20) * 0.15) * Math.cos((x - 20) * 0.04));
        ctx.fillStyle = cYellow;
        ctx.fillRect(x, mid + amp, 1, 1);
        ctx.fillStyle = cCyan;
        ctx.fillRect(x, mid - amp, 1, 1);
      }
    } else {
      drawBitmapString(ctx, 16, 44, "[SYSTEM SETUP]  ROLAND S-760 SYSTEM VERSION 2.24", cWhite, cBlue);
      for (let x = 16; x < 624; x++) {
        ctx.fillStyle = cWhite;
        ctx.fillRect(x, 54, 1, 1);
      }

      drawBitmapString(ctx, 20, 58,  "1. HOST SCSI ID:     [ 7 ] (S-760 INITIATOR ID)", cWhite, cBlue);
      drawBitmapString(ctx, 20, 70,  "2. BOOT DEVICE:      [ SCSI / FLOPPY AUTO-DETECT ]", cWhite, cBlue);
      drawBitmapString(ctx, 20, 82,  "3. SCSI BUS SCAN:    (BLUESCSI / ZULUSCSI TARGETS 0-6):", cYellow, cBlue);
      drawBitmapString(ctx, 20, 94,  "   ID 0: APPLE CD-ROM 300+ (OPTICAL DRIVE)", cGreen, cBlue);
      drawBitmapString(ctx, 20, 105, "   ID 1: QUANTUM FIREBALL 1080S (1.08 GB HDD)", cGreen, cBlue);
      drawBitmapString(ctx, 20, 116, "   ID 2: --- NO DEVICE ---", cWhite, cBlue);
      drawBitmapString(ctx, 20, 127, "   ID 3: --- NO DEVICE ---", cWhite, cBlue);
      drawBitmapString(ctx, 20, 138, "   ID 4: --- NO DEVICE ---", cWhite, cBlue);
      drawBitmapString(ctx, 20, 149, "   ID 5: --- NO DEVICE ---", cWhite, cBlue);
      drawBitmapString(ctx, 20, 160, "   ID 6: --- NO DEVICE ---", cWhite, cBlue);
      drawBitmapString(ctx, 20, 174, "4. MASTER TUNE:      [ 440.0 HZ ]  OUTPUT LEVEL: [ +4 DBU ]", cWhite, cBlue);
      drawBitmapString(ctx, 20, 186, "5. WAVE MEMORY:      [ 32 MBYTES OK (2X 16MB SIMM) ]", cWhite, cBlue);
      drawBitmapString(ctx, 20, 198, "6. OPTION BOARD:     [ OP-760-2 VIDEO BOARD INSTALLED ]", cWhite, cBlue);
    }

    // 6. Bottom Context Ribbon (White Background y = 222..239)
    ctx.fillStyle = cWhite;
    ctx.fillRect(0, 222, W, 18);
    drawBitmapString(ctx, 20, 226, "ALLON", cBlack, cWhite);
    drawBitmapString(ctx, 170, 226, "CONVLD", cBlack, cWhite);
    drawBitmapString(ctx, 330, 226, "ON OFF", cBlack, cWhite);
    drawBitmapString(ctx, 470, 226, "VOLINFO", cBlack, cWhite);

    // 7. Draw Authentic Roland Crosshair Cursor (+) at mousePos
    const { x, y } = mousePos;
    ctx.fillStyle = cWhite;
    for (let dx = -4; dx <= 4; dx++) {
      ctx.fillRect(x + dx, y, 1, 1);
    }
    for (let dy = -4; dy <= 4; dy++) {
      ctx.fillRect(x, y + dy, 1, 1);
    }

  }, [state, mousePos]);

  return (
    <div className="relative flex flex-col items-center select-none">
      {/* Vintage Studio 4:3 CRT Monitor Housing (Roland OP-760 Video Display) */}
      <div className="relative flex flex-col items-center bg-gradient-to-b from-[#2b2e35] via-[#202227] to-[#17191d] p-3.5 sm:p-5 rounded-2xl border-2 border-[#3d424c] shadow-[0_20px_50px_rgba(0,0,0,0.95),inset_0_1px_2px_rgba(255,255,255,0.15)]">
        {/* Top Monitor Bevel with Heat Vents */}
        <div className="w-full flex items-center justify-between px-3 pb-2.5">
          {/* Roland Color Monitor Badge */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-black italic tracking-tighter text-neutral-200 font-sans drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)]">
              Roland
            </span>
            <span className="text-[9px] font-mono font-bold tracking-widest text-neutral-400 uppercase bg-[#14161a] px-1.5 py-0.5 rounded border border-neutral-700">
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
