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
  '^': [0x18, 0x3c, 0x7e, 0xff, 0x00, 0x00, 0x00, 0x00],
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

// Draw S-760 Slider Widget: [---------▲---------] +Value
function drawSlider(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  posRatio: number, // 0.0 to 1.0 (0.5 is center)
  cWhite: string,
  cRed: string
) {
  // Left bracket
  ctx.fillStyle = cWhite;
  ctx.fillRect(x, y, 2, 7);
  // Right bracket
  ctx.fillRect(x + width - 2, y, 2, 7);
  // Horizontal center track line
  ctx.fillRect(x + 2, y + 3, width - 4, 1);

  // Red pointer triangle ▲
  const triX = Math.floor(x + 4 + (width - 10) * Math.max(0, Math.min(1, posRatio)));
  ctx.fillStyle = cRed;
  ctx.fillRect(triX + 2, y + 1, 1, 1);
  ctx.fillRect(triX + 1, y + 2, 3, 1);
  ctx.fillRect(triX, y + 3, 5, 2);
  ctx.fillRect(triX, y + 5, 5, 2);
}

// Draw 61-Key Graphical Keyboard
function drawGraphicKeyboard(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  highlightRanges?: Array<{ startKey: number; endKey: number; color: string }>
) {
  const numWhiteKeys = 36;
  const keyWidth = width / numWhiteKeys;

  // Background base
  ctx.fillStyle = '#0a0a0c';
  ctx.fillRect(x, y, width, height);

  // 1. Draw Split Zone Bars above keys if any
  if (highlightRanges) {
    highlightRanges.forEach((range) => {
      const startX = x + (range.startKey / 61) * width;
      const endX = x + (range.endKey / 61) * width;
      ctx.fillStyle = range.color;
      ctx.fillRect(Math.floor(startX), y - 4, Math.max(2, Math.floor(endX - startX)), 3);
    });
  }

  // 2. White keys
  ctx.fillStyle = '#ffffff';
  for (let i = 0; i < numWhiteKeys; i++) {
    const kx = Math.floor(x + i * keyWidth);
    const kw = Math.floor(keyWidth) - 1;
    ctx.fillRect(kx, y, kw, height);
  }

  // 3. Black keys pattern for 36 white keys (5 octaves)
  // Pattern in an octave: [0, 1, 3, 4, 5] (C#, D#, F#, G#, A#)
  const blackKeyOffsets = [0.65, 1.65, 3.65, 4.65, 5.65];
  const blackHeight = Math.floor(height * 0.6);
  const blackWidth = Math.max(2, Math.floor(keyWidth * 0.65));

  ctx.fillStyle = '#000000';
  for (let oct = 0; oct < 5; oct++) {
    const octBase = oct * 7;
    for (const offset of blackKeyOffsets) {
      if (octBase + offset < numWhiteKeys) {
        const bx = Math.floor(x + (octBase + offset) * keyWidth);
        ctx.fillRect(bx, y, blackWidth, blackHeight);
      }
    }
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
  const [subPage, setSubPage] = useState<number>(0);
  const [activeModal, setActiveModal] = useState<'NONE' | 'MARK' | 'JUMP' | 'COM' | 'MENU'>('NONE');

  // Reset subPage and modal when top-level mode changes
  useEffect(() => {
    setSubPage(0);
    setActiveModal('NONE');
  }, [state.mode]);

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

    // If a modal is currently open, handle modal item clicks or dismiss
    if (activeModal !== 'NONE') {
      // Check for click inside modal
      if (activeModal === 'MARK' || activeModal === 'JUMP') {
        if (x >= 160 && x <= 480 && y >= 45 && y <= 205) {
          const itemIdx = Math.floor((y - 65) / 13);
          if (itemIdx >= 0 && itemIdx < 10) {
            // Jump to selected screen
            if (itemIdx === 0) onSetMode('PERF');
            else if (itemIdx === 1) onSetMode('DISK');
            else if (itemIdx === 4) { onSetMode('PATCH'); setSubPage(1); }
            else if (itemIdx === 5) { onSetMode('PART'); setSubPage(3); }
            else if (itemIdx === 9) { onSetMode('PATCH'); setSubPage(3); }
            setActiveModal('NONE');
            onEventEmit('CRT_MODAL_SELECT', { modal: activeModal, index: itemIdx });
            return;
          }
        }
      } else if (activeModal === 'COM') {
        if (x >= 440 && x <= 600 && y >= 40 && y <= 160) {
          const itemIdx = Math.floor((y - 50) / 16);
          if (itemIdx >= 0 && itemIdx < 6) {
            setActiveModal('NONE');
            onEventEmit('CRT_COM_SELECT', { index: itemIdx });
            return;
          }
        }
      } else if (activeModal === 'MENU') {
        if (x >= 80 && x <= 260 && y >= 40 && y <= 180) {
          const itemIdx = Math.floor((y - 50) / 16);
          if (itemIdx >= 0 && itemIdx < 7) {
            setSubPage(itemIdx % 4);
            setActiveModal('NONE');
            onEventEmit('CRT_MENU_SELECT', { index: itemIdx });
            return;
          }
        }
      }
      // Clicked outside modal -> dismiss
      setActiveModal('NONE');
      return;
    }

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

    // Sub-Ribbon Click (y: 28 to 39)
    if (y >= 28 && y <= 39) {
      // Red badge click (e.g. [Pform], [Patch], [Part1], [Disk])
      if (x >= 180 && x <= 270) {
        setActiveModal(activeModal === 'MENU' ? 'NONE' : 'MENU');
        return;
      }
      // Subscreen Title click -> cycle subpage
      if (x >= 16 && x <= 170) {
        if (state.mode === 'PATCH') setSubPage((subPage + 1) % 4);
        else if (state.mode === 'PART') setSubPage((subPage + 1) % 6);
        return;
      }
      // Mark Click
      if (x >= 360 && x <= 420) {
        setActiveModal(activeModal === 'MARK' ? 'NONE' : 'MARK');
        return;
      }
      // Jump Click
      if (x >= 425 && x <= 485) {
        setActiveModal(activeModal === 'JUMP' ? 'NONE' : 'JUMP');
        return;
      }
      // Com Click
      if (x >= 490 && x <= 560) {
        setActiveModal(activeModal === 'COM' ? 'NONE' : 'COM');
        return;
      }
    }

    // Patch rows click in Perform or Disk (y: 68 to 218)
    if (y >= 68 && y <= 218 && x >= 12 && x <= 460) {
      if (state.mode === 'PERF') {
        const rowIdx = Math.floor((y - 68) / 10);
        if (rowIdx >= 0 && rowIdx < 8) {
          if (onSelectPatchIndex) onSelectPatchIndex(rowIdx);
          onEventEmit('CRT_PERF_PART_CLICK', { index: rowIdx });
        }
      } else if (state.mode === 'DISK') {
        const rowIdx = Math.floor((y - 68) / 9.5);
        if (rowIdx >= 0 && rowIdx < 16) {
          if (onSelectPatchIndex) onSelectPatchIndex(rowIdx);
          onEventEmit('CRT_DISK_ROW_CLICK', { index: rowIdx });
        }
      }
      return;
    }

    // Bottom Soft Ribbon Click (y: 222 to 240)
    if (y >= 222 && y <= 240) {
      const softIdx = Math.floor(x / (640 / 5));
      if (softIdx >= 0 && softIdx < 5) {
        onSoftKey(softIdx);
        // Also allow soft buttons to cycle subpages in Patch/Part modes
        if (state.mode === 'PATCH') {
          if (softIdx < 4) setSubPage(softIdx);
        } else if (state.mode === 'PART') {
          if (softIdx < 5) setSubPage(softIdx);
        }
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

    // Authentic Roland S-760 10-Pen CRT Palette (Exact match to hardware photos)
    const cBlack   = '#000000'; // Pen 0
    const cWhite   = '#ffffff'; // Pen 1
    const cBlue    = '#0000c0'; // Pen 2: Authentic S-760 Royal Blue
    const cGreen   = '#00c850'; // Pen 3: Status Green
    const cYellow  = '#ffe600'; // Pen 4: Parameter & Selection Yellow
    const cRed     = '#dc3c14'; // Pen 5: Tab Selection Outline & Muted Badge Red
    const cLtGray  = '#bec3cd'; // Pen 6: Subheader Light Gray Ribbon
    const cCyan    = '#00dcdc'; // Pen 8: Values & Cyan Function Keys

    // 1. Fill entire CRT workspace with authentic Roland Royal Blue (#0000C0)
    ctx.fillStyle = cBlue;
    ctx.fillRect(0, 0, W, H);

    // 2. Top Status Bar (Status Green y = 0..13)
    ctx.fillStyle = cGreen;
    ctx.fillRect(0, 0, W, 14);
    
    // Top right help text depending on active modal or mode
    let topHelp = "---/---";
    if (activeModal !== 'NONE') {
      topHelp = "Exit/Exit";
    } else if (state.mode === 'PERF') {
      topHelp = "Dec/Inc";
    } else if (state.mode === 'PATCH') {
      topHelp = subPage === 1 ? "--/MIDISel" : "Dec/Inc";
    } else if (state.mode === 'PART') {
      topHelp = "Dec/Inc";
    }

    drawBitmapString(ctx, 8, 3, "Volume[ - :              ] ID:01", cBlack, cGreen);
    drawBitmapString(ctx, 520, 3, topHelp, cBlack, cGreen);

    // 3. Mode Ribbon (White Background y = 14..27)
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
    const activeTab = modeIdxMap[state.mode] ?? 0;

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

    let subTitle = "Perform Play 1";
    let badgeText = "Pform";
    if (state.mode === 'PERF') {
      subTitle = "Perform Play 1";
      badgeText = "Pform";
    } else if (state.mode === 'PATCH') {
      const patchSubPages = ["Patch Common", "Patch Split", "Patch Control", "Patch Q-Sampling"];
      subTitle = patchSubPages[subPage] || "Patch Common";
      badgeText = "Patch";
    } else if (state.mode === 'PART') {
      const partSubPages = ["Partial Common", "Partial SMT", "Partial TVF", "Partial TVA", "Partial LFO", "Partial Q-Sampling"];
      subTitle = partSubPages[subPage] || "Partial Common";
      badgeText = "Part1";
    } else if (state.mode === 'SAMPLE') {
      subTitle = subPage === 0 ? "Sample Info" : "Sample Loop";
      badgeText = "Samp1";
    } else if (state.mode === 'DISK') {
      subTitle = "Disk Load";
      badgeText = "Disk";
    } else if (state.mode === 'SYSTEM') {
      subTitle = "System SCSI";
      badgeText = "Systm";
    }

    drawBitmapString(ctx, 16, 30, subTitle, cBlack, cLtGray);
    
    // Red Badge
    ctx.fillStyle = cRed;
    ctx.fillRect(200, 29, 44, 10);
    drawBitmapString(ctx, 204, 30, badgeText, cWhite, cRed);

    // Separators and buttons
    ctx.fillStyle = cBlack;
    ctx.fillRect(360, 28, 1, 12);
    drawBitmapString(ctx, 372, 30, "Mark", cBlack, cLtGray);
    ctx.fillRect(425, 28, 1, 12);
    drawBitmapString(ctx, 437, 30, "Jump", cBlack, cLtGray);
    ctx.fillRect(490, 28, 1, 12);
    drawBitmapString(ctx, 502, 30, "Com", cCyan, cLtGray);

    // 5. Main Screen Content Area (y = 40..221)
    if (state.mode === 'PERF') {
      // -------------------------------------------------------------
      // PERFORM PLAY 1 (perform-1.jpeg)
      // -------------------------------------------------------------
      drawBitmapString(ctx, 16, 44, "PRM: 01 JP-8 MULTI SET", cWhite, cBlue);
      drawBitmapString(ctx, 340, 44, "Master: 127", cCyan, cBlue);

      // Yellow Table Header
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 55, 480, 10);
      drawBitmapString(ctx, 16, 56, "Part  Patch Name          MIDI-Ch  Output  Pan  Level", cBlack, cYellow);

      // 8 Part Rows (y = 67 to 147)
      const perfParts = [
        { part: ' 1', patch: 'P11: JP-8 BRASS 1', ch: '01', out: '1-2', pan: '<0>', lvl: '127' },
        { part: ' 2', patch: 'P12: JP-8 STRGS 1', ch: '02', out: '1-2', pan: 'L15', lvl: '110' },
        { part: ' 3', patch: 'P13: VP STRINGS 1', ch: '03', out: '1-2', pan: 'R15', lvl: '105' },
        { part: ' 4', patch: 'P14: VP CHOIR 1  ', ch: '04', out: '1-2', pan: '<0>', lvl: '090' },
        { part: ' 5', patch: 'P15: SYNTH 1     ', ch: '05', out: '1-2', pan: '<0>', lvl: '100' },
        { part: ' 6', patch: 'P16: SYNTH 2     ', ch: '06', out: '1-2', pan: '<0>', lvl: '100' },
        { part: ' 7', patch: 'P17: SYNTH 3     ', ch: '07', out: '1-2', pan: '<0>', lvl: '100' },
        { part: ' 8', patch: 'P18: SYNTH 4     ', ch: '08', out: '1-2', pan: '<0>', lvl: '100' },
      ];

      perfParts.forEach((p, idx) => {
        const py = 67 + idx * 10;
        const isSelected = idx === 0;
        const color = isSelected ? cYellow : cWhite;
        drawBitmapString(ctx, 16, py, `${p.part}   ${p.patch}    ${p.ch}       ${p.out}    ${p.pan}  ${p.lvl}`, color, cBlue);
      });

      // Right Side Master Level Meter Box
      ctx.fillStyle = cYellow;
      ctx.fillRect(504, 55, 120, 10);
      drawBitmapString(ctx, 524, 56, "Peak Level", cBlack, cYellow);

      // Meter Box background
      ctx.fillStyle = cBlack;
      ctx.fillRect(504, 68, 120, 78);
      // Meter segments
      for (let s = 0; s < 12; s++) {
        const my = 136 - s * 6;
        const isGreen = s < 8;
        const isYellow = s >= 8 && s < 10;
        const segColor = isGreen ? cGreen : isYellow ? cYellow : cRed;
        ctx.fillStyle = segColor;
        ctx.fillRect(520, my, 40, 4);
        ctx.fillRect(568, my, 40, 4);
      }
      drawBitmapString(ctx, 510, 72, "L", cWhite, cBlack);
      drawBitmapString(ctx, 612, 72, "R", cWhite, cBlack);

      // Lower Area: Keyboard Split preview (y = 156..214)
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 150, 612, 10);
      drawBitmapString(ctx, 16, 151, "Keyboard Part Map (C-1 to G9)", cBlack, cYellow);
      drawGraphicKeyboard(ctx, 12, 166, 612, 48, [
        { startKey: 0, endKey: 24, color: cCyan },
        { startKey: 25, endKey: 42, color: cYellow },
        { startKey: 43, endKey: 61, color: cRed },
      ]);

    } else if (state.mode === 'PATCH') {
      // -------------------------------------------------------------
      // PATCH MODE SCREENS (patch-1 to patch-4)
      // -------------------------------------------------------------
      if (subPage === 0) {
        // --- PATCH COMMON (patch-1.jpeg) ---
        // Yellow banner "Parameter" & "Information"
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 300, 10);
        drawBitmapString(ctx, 16, 45, "Parameter", cBlack, cYellow);

        ctx.fillStyle = cYellow;
        ctx.fillRect(324, 44, 300, 10);
        drawBitmapString(ctx, 328, 45, "Information", cBlack, cYellow);

        // Parameters left
        drawBitmapString(ctx, 16, 60, "Patch Name:   [ 01 JP-8 BRASS 1 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 75, "1Shot Mode:   [ Off ]  (Off, On)", cWhite, cBlue);
        drawBitmapString(ctx, 16, 90, "Bend Range:   Up: [ +2 ]  Down: [ -2 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 105,"Tone Assign:  [ Poly ]", cWhite, cBlue);

        // Sliders on right (y = 60..135)
        drawBitmapString(ctx, 328, 60, "Cutoff Offset:", cWhite, cBlue);
        drawSlider(ctx, 440, 60, 120, 0.5, cWhite, cRed);
        drawBitmapString(ctx, 570, 60, "+0", cCyan, cBlue);

        drawBitmapString(ctx, 328, 76, "Reso Offset:  ", cWhite, cBlue);
        drawSlider(ctx, 440, 76, 120, 0.5, cWhite, cRed);
        drawBitmapString(ctx, 570, 76, "+0", cCyan, cBlue);

        drawBitmapString(ctx, 328, 92, "Attack Offset:", cWhite, cBlue);
        drawSlider(ctx, 440, 92, 120, 0.5, cWhite, cRed);
        drawBitmapString(ctx, 570, 92, "+0", cCyan, cBlue);

        drawBitmapString(ctx, 328, 108, "Release Off:  ", cWhite, cBlue);
        drawSlider(ctx, 440, 108, 120, 0.5, cWhite, cRed);
        drawBitmapString(ctx, 570, 108, "+0", cCyan, cBlue);

        drawBitmapString(ctx, 328, 124, "V-Sens Offset:", cWhite, cBlue);
        drawSlider(ctx, 440, 124, 120, 0.5, cWhite, cRed);
        drawBitmapString(ctx, 570, 124, "+0", cCyan, cBlue);

        // Lower split zone summary
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 144, 612, 10);
        drawBitmapString(ctx, 16, 145, "Partial Key Assignment Overview", cBlack, cYellow);
        drawGraphicKeyboard(ctx, 12, 162, 612, 52, [
          { startKey: 0, endKey: 30, color: cCyan },
          { startKey: 31, endKey: 61, color: cYellow },
        ]);

      } else if (subPage === 1) {
        // --- PATCH SPLIT (patch-2.jpeg) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "Partial Name    L.P  U.P  Type   Sample Name         Time   Key", cBlack, cYellow);

        drawBitmapString(ctx, 16, 58, "1: JP-8 BRASS L C-1  B3   Poly   [1] JP-8_B1_L       02.4s  C4", cWhite, cBlue);
        drawBitmapString(ctx, 16, 72, "2: JP-8 BRASS R C-1  B3   Poly   [2] JP-8_B1_R       02.4s  C4", cWhite, cBlue);
        drawBitmapString(ctx, 16, 86, "3: JP-8 BRASS H C4   G9   Poly   [3] JP-8_B2_L       02.8s  G5", cWhite, cBlue);
        drawBitmapString(ctx, 16, 100,"4: --- OFF ---  ---  ---  ----   ---                 00.0s  --", cLtGray, cBlue);

        // Keyboard split graphic in middle
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 116, 612, 10);
        drawBitmapString(ctx, 16, 117, "Split Point Zone Monitor", cBlack, cYellow);
        drawGraphicKeyboard(ctx, 12, 134, 612, 80, [
          { startKey: 0, endKey: 30, color: cCyan },
          { startKey: 0, endKey: 30, color: cRed },
          { startKey: 31, endKey: 61, color: cYellow },
        ]);

      } else if (subPage === 2) {
        // --- PATCH CONTROL (patch-3.jpeg) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "Patch Modulation & Controller Matrix", cBlack, cYellow);

        drawBitmapString(ctx, 16, 60, "SMT Ctrl Sel:  [ Modulation (CC#01) ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 75, "Pitch Bend Up: [ +2 ]     Bend Down: [ -2 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 90, "Aftertouch:    [ TVF Cutoff +30 ]", cWhite, cBlue);

        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 110, 612, 10);
        drawBitmapString(ctx, 16, 111, "LFO Depth & Rate Modulation Matrix", cBlack, cYellow);

        drawBitmapString(ctx, 16, 126, "LFO-Pitch Depth: [ +15 ]", cWhite, cBlue);
        drawSlider(ctx, 220, 126, 120, 0.6, cWhite, cRed);

        drawBitmapString(ctx, 16, 142, "LFO-TVF Depth:   [ +00 ]", cWhite, cBlue);
        drawSlider(ctx, 220, 142, 120, 0.5, cWhite, cRed);

        drawBitmapString(ctx, 16, 158, "LFO-TVA Depth:   [ +25 ]", cWhite, cBlue);
        drawSlider(ctx, 220, 158, 120, 0.7, cWhite, cRed);

        drawBitmapString(ctx, 16, 174, "LFO-PAN Depth:   [ +10 ]", cWhite, cBlue);
        drawSlider(ctx, 220, 174, 120, 0.58, cWhite, cRed);

      } else {
        // --- PATCH Q-SAMPLING (patch-4.jpeg) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "[ Pitch ]              [ TVF ]              [ TVA ]", cBlack, cYellow);

        drawBitmapString(ctx, 16, 60, "Start: 0000,000", cWhite, cBlue);
        drawBitmapString(ctx, 16, 75, "Loop:  0048,200", cYellow, cBlue);
        drawBitmapString(ctx, 16, 90, "End:   0130,560", cWhite, cBlue);
        drawBitmapString(ctx, 16, 105,"Mode:  Forward", cWhite, cBlue);
        drawBitmapString(ctx, 16, 120,"Key:   C4", cWhite, cBlue);

        // TVF Group
        drawBitmapString(ctx, 230, 60, "Cutoff: 84", cWhite, cBlue);
        drawBitmapString(ctx, 230, 75, "Reso:   32", cWhite, cBlue);
        drawBitmapString(ctx, 230, 90, "KF:   +1.0", cWhite, cBlue);

        // TVA Group
        drawBitmapString(ctx, 440, 60, "Level: 127", cWhite, cBlue);
        drawBitmapString(ctx, 440, 75, "Pan:   <0>", cWhite, cBlue);
        drawBitmapString(ctx, 440, 90, "E.Mode:Mono", cWhite, cBlue);

        // Waveform preview box
        ctx.fillStyle = cBlack;
        ctx.fillRect(12, 140, 612, 75);
        for (let wx = 14; wx < 620; wx++) {
          const wy = 177 + Math.floor(22 * Math.sin((wx - 14) * 0.12) * Math.cos((wx - 14) * 0.03));
          ctx.fillStyle = cCyan;
          ctx.fillRect(wx, wy, 1, 1);
        }
      }

    } else if (state.mode === 'PART') {
      // -------------------------------------------------------------
      // PARTIAL MODE SCREENS (partial-1 to partial-6)
      // -------------------------------------------------------------
      if (subPage === 0) {
        // --- PARTIAL COMMON (partial-1.jpeg) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "Partial Common Parameters (Partial 1: JP-8 BRASS L)", cBlack, cYellow);

        drawBitmapString(ctx, 16, 60, "Partial Level:  [ 127 ]", cWhite, cBlue);
        drawSlider(ctx, 220, 60, 140, 1.0, cWhite, cRed);

        drawBitmapString(ctx, 16, 75, "Panning:        [  <0> ]", cWhite, cBlue);
        drawSlider(ctx, 220, 75, 140, 0.5, cWhite, cRed);

        drawBitmapString(ctx, 16, 90, "Output Assign:  [  1-2 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 105,"Coarse Tune:    [   +0 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 120,"Fine Tune:      [   +0 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 135,"SMT Vel Ctrl:   [   On ] (Off, On)", cWhite, cBlue);

        // Keyboard diagram at bottom
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 152, 612, 10);
        drawBitmapString(ctx, 16, 153, "Key Range: C-1 to B3", cBlack, cYellow);
        drawGraphicKeyboard(ctx, 12, 168, 612, 46, [
          { startKey: 0, endKey: 30, color: cCyan },
        ]);

      } else if (subPage === 1) {
        // --- PARTIAL SMT (partial-2.jpeg - Velocity Split Matrix) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "Partial SMT Velocity Crossfade / Switch", cBlack, cYellow);

        drawBitmapString(ctx, 16, 58, "1: Ky+ 107  1  126   0  53 (Cyan Bar)", cCyan, cBlue);
        drawBitmapString(ctx, 16, 72, "2: Ky+ 127 73  127  53   0 (Red Bar)", cRed, cBlue);
        drawBitmapString(ctx, 16, 86, "Control Mode: Velocity Crossfade [ Vel-XFade ]", cWhite, cBlue);

        // Black box with Cyan & Red velocity lines/boxes (y = 104..215)
        ctx.fillStyle = cBlack;
        ctx.fillRect(12, 102, 612, 114);

        // Grid dotted lines
        for (let gx = 12; gx < 624; gx += 40) {
          for (let gy = 104; gy < 214; gy += 8) {
            ctx.fillStyle = '#182438';
            ctx.fillRect(gx, gy, 1, 1);
          }
        }

        // Cyan Velocity zone 1
        ctx.fillStyle = cCyan;
        ctx.fillRect(24, 180, 280, 3);
        ctx.fillRect(24, 120, 3, 60);
        ctx.fillRect(304, 120, 3, 60);
        // Slope line
        for (let lx = 24; lx < 304; lx++) {
          const ly = 120 + Math.floor((lx - 24) * 0.2);
          ctx.fillRect(lx, ly, 1, 1);
        }
        drawBitmapString(ctx, 32, 125, "Layer 1 (0-107)", cCyan, cBlack);

        // Red Velocity zone 2
        ctx.fillStyle = cRed;
        ctx.fillRect(280, 180, 330, 3);
        ctx.fillRect(280, 115, 3, 65);
        ctx.fillRect(610, 115, 3, 65);
        for (let rx = 280; rx < 610; rx++) {
          const ry = 180 - Math.floor((rx - 280) * 0.2);
          ctx.fillRect(rx, ry, 1, 1);
        }
        drawBitmapString(ctx, 310, 125, "Layer 2 (73-127)", cRed, cBlack);

      } else if (subPage === 2) {
        // --- PARTIAL TVF (partial-3.jpeg - Filter Envelope) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "TVF Filter Parameters & Graphic Envelope", cBlack, cYellow);

        drawBitmapString(ctx, 16, 58, "Cutoff Freq: [  84 ]     Resonance: [  32 ]     Cutoff KF: [ +1.0 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 72, "Vel-Curve:   [ 1:/ ]     V-Sens:    [ +45 ]     Time KF:   [    0 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 86, "Envelope Points: [1] 0 127   [2] 74 45   [3] 102 0   [4] 127 0", cCyan, cBlue);

        // Black box with TVF graphic envelope (y = 100..215)
        ctx.fillStyle = cBlack;
        ctx.fillRect(12, 100, 612, 116);

        // Envelope grid
        for (let gx = 12; gx < 624; gx += 48) {
          for (let gy = 102; gy < 214; gy += 10) {
            ctx.fillStyle = '#142030';
            ctx.fillRect(gx, gy, 1, 1);
          }
        }

        // Sustain marker line (Green)
        ctx.fillStyle = cGreen;
        ctx.fillRect(380, 102, 2, 112);
        drawBitmapString(ctx, 370, 106, "SUS", cGreen, cBlack);

        // White Envelope Curve Line
        const tvfPoints = [
          { x: 30, y: 200 },
          { x: 40, y: 115 },
          { x: 180, y: 155 },
          { x: 380, y: 200 },
          { x: 580, y: 200 },
        ];
        ctx.strokeStyle = cWhite;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(tvfPoints[0].x, tvfPoints[0].y);
        for (let p = 1; p < tvfPoints.length; p++) {
          ctx.lineTo(tvfPoints[p].x, tvfPoints[p].y);
        }
        ctx.stroke();

        // Cyan node squares ▪
        tvfPoints.forEach((pt, pidx) => {
          ctx.fillStyle = cCyan;
          ctx.fillRect(pt.x - 2, pt.y - 2, 5, 5);
          drawBitmapString(ctx, pt.x - 4, pt.y - 12, `[${pidx + 1}]`, cCyan, cBlack);
        });

      } else if (subPage === 3) {
        // --- PARTIAL TVA (partial-4.jpeg - Amplitude Envelope) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "TVA Amplifier Parameters & Graphic Envelope", cBlack, cYellow);

        drawBitmapString(ctx, 16, 58, "TVA Level:   [ 127 ]     Vel-Curve: [ 1:/ ]     V-Sens:  [ +30 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 72, "Level KF:    [   0 ]     Time KF:   [   0 ]     Pan:     [  <0> ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 86, "Envelope Points: [1] 0 127   [2] 127 125   [3] 99 0   [4] 20 ---", cCyan, cBlue);

        // Black box with TVA graphic envelope (y = 100..215)
        ctx.fillStyle = cBlack;
        ctx.fillRect(12, 100, 612, 116);

        // Dotted grid
        for (let gx = 12; gx < 624; gx += 48) {
          for (let gy = 102; gy < 214; gy += 10) {
            ctx.fillStyle = '#142030';
            ctx.fillRect(gx, gy, 1, 1);
          }
        }

        // Green sustain line
        ctx.fillStyle = cGreen;
        ctx.fillRect(420, 102, 2, 112);
        drawBitmapString(ctx, 410, 106, "SUS", cGreen, cBlack);

        // White TVA envelope line
        const tvaPoints = [
          { x: 30, y: 200 },
          { x: 50, y: 112 },
          { x: 260, y: 116 },
          { x: 420, y: 200 },
          { x: 590, y: 200 },
        ];
        ctx.strokeStyle = cWhite;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(tvaPoints[0].x, tvaPoints[0].y);
        for (let p = 1; p < tvaPoints.length; p++) {
          ctx.lineTo(tvaPoints[p].x, tvaPoints[p].y);
        }
        ctx.stroke();

        // Cyan node squares
        tvaPoints.forEach((pt, pidx) => {
          ctx.fillStyle = cCyan;
          ctx.fillRect(pt.x - 2, pt.y - 2, 5, 5);
          drawBitmapString(ctx, pt.x - 4, pt.y - 12, `[${pidx + 1}]`, cCyan, cBlack);
        });

      } else if (subPage === 4) {
        // --- PARTIAL LFO (partial-5.jpeg) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "Partial LFO Generator & Waveform Control", cBlack, cYellow);

        drawBitmapString(ctx, 16, 58, "Waveform: [ Sin ] (Sin, Tri, SwUP, SwDW, Squ, Rnd, B.UP, B.DW)", cWhite, cBlue);
        drawBitmapString(ctx, 16, 72, "Rate:     [  64 ]     Detune: [   0 ]     Delay: [  10 ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 86, "Key Fol:  [   0 ]     KeySync:[  On ]     Offset:[   0 ]", cWhite, cBlue);

        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 102, 612, 10);
        drawBitmapString(ctx, 16, 103, "LFO Modulation Depths", cBlack, cYellow);

        drawBitmapString(ctx, 16, 118, "Pitch Depth: [ +20 ]", cWhite, cBlue);
        drawSlider(ctx, 200, 118, 120, 0.65, cWhite, cRed);

        drawBitmapString(ctx, 16, 134, "TVF Depth:   [  +0 ]", cWhite, cBlue);
        drawSlider(ctx, 200, 134, 120, 0.50, cWhite, cRed);

        drawBitmapString(ctx, 16, 150, "TVA Depth:   [  +0 ]", cWhite, cBlue);
        drawSlider(ctx, 200, 150, 120, 0.50, cWhite, cRed);

        drawBitmapString(ctx, 16, 166, "PAN Depth:   [ +15 ]", cWhite, cBlue);
        drawSlider(ctx, 200, 166, 120, 0.60, cWhite, cRed);

        // LFO Wave visualizer
        ctx.fillStyle = cBlack;
        ctx.fillRect(360, 118, 260, 60);
        for (let lx = 362; lx < 618; lx++) {
          const ly = 148 + Math.floor(18 * Math.sin((lx - 362) * 0.1));
          ctx.fillStyle = cCyan;
          ctx.fillRect(lx, ly, 1, 1);
        }

      } else {
        // --- PARTIAL Q-SAMPLING (partial-6.jpeg) ---
        ctx.fillStyle = cYellow;
        ctx.fillRect(12, 44, 612, 10);
        drawBitmapString(ctx, 16, 45, "Partial Q-Sampling & Sample Slice Points", cBlack, cYellow);

        drawBitmapString(ctx, 16, 58, "Sample Name:  [ W01: JP-8_BRASS_44K ]", cWhite, cBlue);
        drawBitmapString(ctx, 16, 72, "Start Point:  0000,000      Loop Start: 0048,200", cWhite, cBlue);
        drawBitmapString(ctx, 16, 86, "End Point:    0130,560      Loop Mode:  Forward", cWhite, cBlue);

        // Waveform box
        ctx.fillStyle = cBlack;
        ctx.fillRect(12, 104, 612, 110);
        for (let wx = 14; wx < 620; wx++) {
          const wy = 159 + Math.floor(25 * Math.sin((wx - 14) * 0.15) * Math.cos((wx - 14) * 0.04));
          ctx.fillStyle = cYellow;
          ctx.fillRect(wx, wy, 1, 1);
        }
      }

    } else if (state.mode === 'DISK') {
      // -------------------------------------------------------------
      // DISK LOAD (DISK-1.jpeg, DISK-2.jpeg)
      // -------------------------------------------------------------
      drawBitmapString(ctx, 24, 44, "TG[Pfom]   ID[All]   CD[FDD:-FloppyDisk-]", cWhite, cBlue);

      // Yellow table header bar (y = 56..65, x = 12..460)
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 448, 10);
      drawBitmapString(ctx, 24, 57, "1files", cBlack, cYellow);
      drawBitmapString(ctx, 340, 57, "Time P#", cBlack, cYellow);

      // 16 File Rows (y = 68 to 208)
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
          drawBitmapString(ctx, 24, Math.floor(ry), row.num, cWhite, cBlue);
          drawBitmapString(ctx, 60, Math.floor(ry), row.name, cWhite, cBlue);
          drawBitmapString(ctx, 350, Math.floor(ry), row.time, cWhite, cBlue);
        } else {
          drawBitmapString(ctx, 24, Math.floor(ry), row.num, cWhite, cBlue);
          drawBitmapString(ctx, 350, Math.floor(ry), row.time, cWhite, cBlue);
        }
      });

      // Right Side Parameter Boxes Stack:
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

    } else if (state.mode === 'SAMPLE') {
      // -------------------------------------------------------------
      // SAMPLE INFO / LOOP
      // -------------------------------------------------------------
      drawBitmapString(ctx, 16, 44, "Sample: W01 JP-8_BRASS_44K.WAV (44.1kHz 16-Bit)", cWhite, cBlue);
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 612, 10);
      drawBitmapString(ctx, 16, 57, "Wave Parameter Information & Loop Settings", cBlack, cYellow);

      drawBitmapString(ctx, 16, 70,  "Orig Key:    C4           Sample Rate: 44.1 kHz", cWhite, cBlue);
      drawBitmapString(ctx, 16, 84,  "Wave Length: 2.95 s       Remaining:   363.8 s", cWhite, cBlue);
      drawBitmapString(ctx, 16, 98,  "Start Point: 0000,000     End Point:   0130,560", cWhite, cBlue);
      drawBitmapString(ctx, 16, 112, "Loop Start:  0048,200     Loop End:    0128,400", cYellow, cBlue);
      drawBitmapString(ctx, 16, 126, "Loop Mode:   Forward      Fine Tune:   +0 cent", cWhite, cBlue);

      // Waveform display graph in Black Box
      ctx.fillStyle = cBlack;
      ctx.fillRect(12, 142, 612, 74);
      for (let x = 14; x < 620; x++) {
        const mid = 179;
        const amp = Math.floor(18.0 * Math.sin((x - 14) * 0.15) * Math.cos((x - 14) * 0.04));
        ctx.fillStyle = cYellow;
        ctx.fillRect(x, mid + amp, 1, 1);
        ctx.fillStyle = cCyan;
        ctx.fillRect(x, mid - amp, 1, 1);
      }

    } else {
      // -------------------------------------------------------------
      // SYSTEM SCSI / CONFIG
      // -------------------------------------------------------------
      drawBitmapString(ctx, 16, 44, "S-760 ROM Version 2.24           Ram:32MB OK", cWhite, cBlue);
      ctx.fillStyle = cYellow;
      ctx.fillRect(12, 56, 612, 10);
      drawBitmapString(ctx, 16, 57, "SCSI Bus Targets Configuration (ID 0-6)", cBlack, cYellow);

      drawBitmapString(ctx, 16, 72,  "S-760 Self SCSI ID:  [ 7 ]", cWhite, cBlue);
      drawBitmapString(ctx, 16, 86,  "Initial Drive:       [ SCSI 0 ]", cWhite, cBlue);
      drawBitmapString(ctx, 16, 100, "Boot Drive:          [ SCSI / Floppy Auto ]", cWhite, cBlue);
      drawBitmapString(ctx, 16, 114, "CDP Driver Type:     [ Apple / Toshiba / Sony ]", cWhite, cBlue);
      drawBitmapString(ctx, 16, 130, "  ID 0: APPLE CD-ROM 300+ (Optical Drive)", cGreen, cBlue);
      drawBitmapString(ctx, 16, 144, "  ID 1: QUANTUM FIREBALL 1080S (1.08 GB HDD)", cGreen, cBlue);
      drawBitmapString(ctx, 16, 158, "  ID 2..6: --- No Device ---", cLtGray, cBlue);
    }

    // 6. Bottom Context Function Keys Ribbon (y = 222..240)
    if (state.mode === 'DISK') {
      // Button 1: [ ] AllOn
      ctx.fillStyle = cWhite;
      ctx.fillRect(12, 222, 92, 14);
      ctx.fillStyle = cBlack;
      ctx.fillRect(16, 225, 8, 8);
      ctx.fillStyle = cWhite;
      ctx.fillRect(17, 226, 6, 6);
      drawBitmapString(ctx, 28, 225, "AllOn", cBlack, cWhite);

      // Button 2: Solid Cyan button with '---'
      ctx.fillStyle = cCyan;
      ctx.fillRect(120, 222, 100, 14);
      drawBitmapString(ctx, 156, 225, "---", cBlack, cCyan);

      // Button 3: Solid White button with 'Load'
      ctx.fillStyle = cWhite;
      ctx.fillRect(236, 222, 100, 14);
      drawBitmapString(ctx, 266, 225, "Load", cBlack, cWhite);

      // Button 4: [ ] OW Off
      ctx.fillStyle = cWhite;
      ctx.fillRect(352, 222, 100, 14);
      ctx.fillStyle = cBlack;
      ctx.fillRect(356, 225, 8, 8);
      ctx.fillStyle = cWhite;
      ctx.fillRect(357, 226, 6, 6);
      drawBitmapString(ctx, 368, 225, "OW Off", cBlack, cWhite);

      // Button 5: Solid White button with 'VolInfo'
      ctx.fillStyle = cWhite;
      ctx.fillRect(468, 222, 122, 14);
      drawBitmapString(ctx, 492, 225, "VolInfo", cBlack, cWhite);

    } else if (state.mode === 'PERF') {
      // Perform Play 1 soft keys (perform-1.jpeg): [ ] KbdOn | Q-Samp | Sol/Mut | PartMap | VolInfo
      const perfBtns = ["[ ] KbdOn", "Q-Samp", "Sol/Mut", "PartMap", "VolInfo"];
      const colW = Math.floor(W / 5);
      perfBtns.forEach((btnTxt, idx) => {
        const bx = idx * colW + 12;
        ctx.fillStyle = cWhite;
        ctx.fillRect(bx, 222, colW - 8, 14);
        drawBitmapString(ctx, bx + 10, 225, btnTxt, cBlack, cWhite);
      });

    } else if (state.mode === 'PATCH') {
      // Patch soft keys: MIDISel | [ ] O.W | Set | --- | ---
      const patchBtns = ["MIDISel", "[ ] O.W", subPage === 1 ? "Set" : "---", "---", "---"];
      const colW = Math.floor(W / 5);
      patchBtns.forEach((btnTxt, idx) => {
        const bx = idx * colW + 12;
        ctx.fillStyle = idx === 0 ? cCyan : cWhite;
        ctx.fillRect(bx, 222, colW - 8, 14);
        drawBitmapString(ctx, bx + 10, 225, btnTxt, cBlack, idx === 0 ? cCyan : cWhite);
      });

    } else if (state.mode === 'PART') {
      // Partial soft keys: [ ] Single | [ ] Mono | --- | --- | ---
      const partBtns = ["[ ] Single", subPage === 1 ? "[ ] Mono" : "---", "---", "Loop", "---"];
      const colW = Math.floor(W / 5);
      partBtns.forEach((btnTxt, idx) => {
        const bx = idx * colW + 12;
        ctx.fillStyle = cWhite;
        ctx.fillRect(bx, 222, colW - 8, 14);
        drawBitmapString(ctx, bx + 10, 225, btnTxt, cBlack, cWhite);
      });

    } else {
      // Default bottom ribbon
      ctx.fillStyle = cWhite;
      ctx.fillRect(0, 222, W, 18);
      let softBtns = ['Info', 'Loop', 'Trun', 'Norm', 'VolInfo'];
      if (state.mode === 'SYSTEM') {
        softBtns = ['SCSI', 'PRM', 'MIDI', 'VolID', 'VolInfo'];
      }
      const colW = Math.floor(W / 5);
      softBtns.forEach((btnTxt, idx) => {
        const bx = idx * colW + 16;
        drawBitmapString(ctx, bx, 226, btnTxt, cBlack, cWhite);
        if (idx < 4) drawBitmapString(ctx, (idx + 1) * colW - 6, 226, "|", cBlack, cWhite);
      });
    }

    // 7. Modals and Overlays (Mark, Jump, Com, Perform Menu)
    if (activeModal === 'MARK' || activeModal === 'JUMP') {
      const title = activeModal === 'MARK' ? "Mark" : "Jump";
      // Centered Modal Window (x = 160..480, y = 45..205)
      ctx.fillStyle = '#0a1020';
      ctx.fillRect(160, 45, 320, 160);
      ctx.fillStyle = cWhite;
      ctx.strokeRect(160, 45, 320, 160);

      // Modal Title Header
      ctx.fillStyle = cYellow;
      ctx.fillRect(160, 45, 320, 14);
      drawBitmapString(ctx, 296, 48, title, cBlack, cYellow);

      // 10 Mark / Jump items (perform-2.jpeg, perform-3.jpeg)
      const markItems = [
        "01: Perform Play 1",
        "02: Disk Load",
        "03: Disk Save",
        "04: System Volume ID",
        "05: *Patch Split",
        "06: *Partial TVA",
        "07: Listen Delete",
        "08: Loop&Smoothing",
        "09: Auto Trun/Norm",
        "10: Patch Q-Sampling",
      ];
      markItems.forEach((item, midx) => {
        const iy = 65 + midx * 13;
        drawBitmapString(ctx, 175, iy, item, cWhite, '#0a1020');
      });

    } else if (activeModal === 'COM') {
      // Command Popup Menu (perform-4.jpeg)
      ctx.fillStyle = '#0a1020';
      ctx.fillRect(440, 40, 160, 120);
      ctx.fillStyle = cWhite;
      ctx.strokeRect(440, 40, 160, 120);

      ctx.fillStyle = cYellow;
      ctx.fillRect(440, 40, 160, 12);
      drawBitmapString(ctx, 490, 42, "Command", cBlack, cYellow);

      const comItems = ["Edit Patch", "Copy", "Delete", "Initialize", "Disk", "CD Player"];
      comItems.forEach((item, cidx) => {
        const cy = 56 + cidx * 16;
        drawBitmapString(ctx, 452, cy, item, cWhite, '#0a1020');
      });

    } else if (activeModal === 'MENU') {
      // Menu Popup (perform-5.jpeg)
      ctx.fillStyle = '#0a1020';
      ctx.fillRect(80, 40, 180, 136);
      ctx.fillStyle = cWhite;
      ctx.strokeRect(80, 40, 180, 136);

      ctx.fillStyle = cYellow;
      ctx.fillRect(80, 40, 180, 12);
      drawBitmapString(ctx, 120, 42, "Perform MENU", cBlack, cYellow);

      const menuItems = ["*Perform Play", "Perform EQ", "MIDI Filter", "Listen Delete", "Perform Utility", "Monitor", "Quick Load"];
      menuItems.forEach((item, midx) => {
        const my = 56 + midx * 16;
        drawBitmapString(ctx, 92, my, item, cWhite, '#0a1020');
      });
    }

    // 8. Draw Authentic Roland Crosshair Mouse Cursor (+) at mousePos
    const { x, y } = mousePos;
    ctx.fillStyle = cWhite;
    for (let dx = -4; dx <= 4; dx++) {
      ctx.fillRect(x + dx, y, 1, 1);
    }
    for (let dy = -4; dy <= 4; dy++) {
      ctx.fillRect(x, y + dy, 1, 1);
    }

  }, [state, diskList, mousePos, subPage, activeModal]);

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
