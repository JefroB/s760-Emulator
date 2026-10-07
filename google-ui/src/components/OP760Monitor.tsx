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
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 380, y: 130 });

  const selectedDisk = diskList[state.gotek.selectedImageIndex] || diskList[0];
  const mountedDisk =
    state.gotek.mountedImageIndex !== null ? diskList[state.gotek.mountedImageIndex] : null;

  const currentDisk = mountedDisk || selectedDisk;

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
      return;
    }

    // Roland S-760 Authentic 10-Pen Palette
    const cBlack   = '#000000';
    const cWhite   = '#ffffff';
    const cBlue    = '#0000c8'; // 2: Roland Royal Blue
    const cGreen   = '#00c850'; // 3: Bright Status Green
    const cYellow  = '#f8d800'; // 4: Yellow Parameter Box
    const cRed     = '#dc3c14'; // 5: Red / Orange Tab Border
    const cLtGray  = '#bec3cd'; // 6: Light Gray Sub-Ribbon
    const cDkNavy  = '#000060'; // 7: Dark Navy
    const cCyan    = '#00dcdc'; // 8: Cyan

    // 1. Fill CRT workspace with Roland Royal Blue (#0000c8)
    ctx.fillStyle = cBlue;
    ctx.fillRect(0, 0, W, H);

    // 2. Top Status Bar (Green Bar y = 0..13)
    ctx.fillStyle = cGreen;
    ctx.fillRect(0, 0, W, 14);

    ctx.font = 'bold 9px monospace';
    ctx.textBaseline = 'top';
    ctx.textAlign = 'left';
    ctx.fillStyle = cBlack;
    ctx.fillText('VOLUME[ - :      ]                 ID:04              ---/---', 6, 3);

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
    const activeTab = modeIdxMap[state.mode] ?? 4;

    ctx.font = 'bold 9px monospace';
    ctx.fillStyle = activeTab === 0 ? cRed : cBlack;
    ctx.fillText('PERFORM', 16, 17);
    ctx.fillStyle = cBlack;
    ctx.fillText('|', 88, 17);

    ctx.fillStyle = activeTab === 1 ? cRed : cBlack;
    ctx.fillText('PATCH', 108, 17);
    ctx.fillStyle = cBlack;
    ctx.fillText('|', 164, 17);

    ctx.fillStyle = activeTab === 2 ? cRed : cBlack;
    ctx.fillText('PARTIAL', 184, 17);
    ctx.fillStyle = cBlack;
    ctx.fillText('|', 256, 17);

    ctx.fillStyle = activeTab === 3 ? cRed : cBlack;
    ctx.fillText('SAMPLE', 276, 17);
    ctx.fillStyle = cBlack;
    ctx.fillText('|', 340, 17);

    ctx.fillStyle = activeTab === 4 ? cRed : cBlack;
    ctx.fillText('DISK', 360, 17);
    ctx.fillStyle = cBlack;
    ctx.fillText('|', 412, 17);

    ctx.fillStyle = activeTab === 5 ? cRed : cBlack;
    ctx.fillText('SYSTEM', 432, 17);

    // Draw active tab red border
    const tabBoxes = [
      [12, 84],
      [102, 156],
      [178, 248],
      [270, 332],
      [352, 402],
      [426, 486],
    ];
    const [bx0, bx1] = tabBoxes[activeTab];
    ctx.strokeStyle = cRed;
    ctx.lineWidth = 1;
    ctx.strokeRect(bx0 + 0.5, 14.5, bx1 - bx0, 13);

    // 4. Context Sub-Ribbon (Light Gray y = 28..39)
    ctx.fillStyle = cLtGray;
    ctx.fillRect(0, 28, W, 12);

    ctx.fillStyle = cBlack;
    if (state.mode === 'DISK') {
      ctx.fillText('CONVERT LD[S]        |  MUTED  |  MARK  |  JUMP  |  COM', 8, 30);
    } else if (state.mode === 'PERF') {
      ctx.fillText('PLAY [PERFORM]       |  MIDI  |  PART  |  SPLIT |  MIX', 8, 30);
    } else if (state.mode === 'PATCH') {
      ctx.fillText('EDIT [PATCH]         |  SPLIT |  LAYER |  V-SW  |  COMMON', 8, 30);
    } else if (state.mode === 'SAMPLE') {
      ctx.fillText('EDIT [SAMPLE]        |  LOOP  |  PITCH |  NORM  |  CONVERT', 8, 30);
    } else if (state.mode === 'SYSTEM') {
      ctx.fillText('SETUP [SYSTEM]       |  MIDI   |  TEST  |  FORMAT|  SAVESYS', 8, 30);
    } else {
      ctx.fillText('EDIT [PARTIAL]       |  TVF   |  TVA   |  ENV   |  LFO', 8, 30);
    }

    // 5. Main Content Area (Blue Canvas y = 40..221)
    if (state.mode === 'DISK') {
      ctx.fillStyle = cWhite;
      ctx.fillText(`[GE PACH]   ART  1]    CD[FDD: -FLOPPYDISK-]`, 16, 44);

      // White line under subheader
      ctx.strokeStyle = cWhite;
      ctx.beginPath();
      ctx.moveTo(16, 54);
      ctx.lineTo(624, 54);
      ctx.stroke();

      // Patch rows
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

        if (i === 5) {
          // Highlight row 6
          ctx.fillStyle = cYellow;
          ctx.fillRect(14, rowY - 1, 160, 9);
          ctx.fillStyle = cBlack;
          ctx.fillText(rowTxt, 16, rowY);
        } else {
          ctx.fillStyle = cWhite;
          ctx.fillText(rowTxt, 16, rowY);
        }
      });

      // Right Parameter Boxes (Yellow filled)
      const drawParamBox = (pbx: number, pby: number, pbw: number, pbh: number, txt: string) => {
        ctx.fillStyle = cYellow;
        ctx.fillRect(pbx, pby, pbw, pbh);
        ctx.fillStyle = cBlack;
        ctx.font = 'bold 9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(txt, pbx + pbw / 2, pby + 2);
        ctx.textAlign = 'left';
      };

      drawParamBox(500, 58, 120, 12, 'INT.');
      drawParamBox(500, 74, 120, 12, '2954SEC');
      drawParamBox(500, 90, 120, 12, 'MARKED');
      drawParamBox(500, 106, 120, 12, '0');
      drawParamBox(500, 122, 120, 12, '+/-');

    } else if (state.mode === 'PERF') {
      ctx.fillStyle = cWhite;
      ctx.fillText('[PERFORM PLAY]  PRM: 01 JP-8 MULTI SET       CD[RAM: 32MB]', 16, 44);
      ctx.strokeStyle = cWhite;
      ctx.beginPath();
      ctx.moveTo(16, 54);
      ctx.lineTo(624, 54);
      ctx.stroke();

      const parts = [
        'PART 1: CH 01 | P11: JP-8 BRASS 1   | VOL: 127 | PAN: <0> | OUT: 1-2',
        'PART 2: CH 02 | P12: JP-8 STRGS 1   | VOL: 110 | PAN: L15 | OUT: 1-2',
        'PART 3: CH 03 | P13: VP STRINGS 1   | VOL: 105 | PAN: R15 | OUT: 1-2',
        'PART 4: CH 04 | P14: VP CHOIR 1     | VOL: 090 | PAN: <0> | OUT: 3-4',
        'PART 5: CH 05 | P15: SYNTH 1        | VOL: 100 | PAN: <0> | OUT: 1-2',
        'PART 6: CH 06 | P16: SYNTH 2        | VOL: 100 | PAN: <0> | OUT: 1-2',
        'PART 7: CH 07 | P17: SYNTH 3        | VOL: 100 | PAN: <0> | OUT: 1-2',
        'PART 8: CH 08 | P18: SYNTH 4        | VOL: 100 | PAN: <0> | OUT: 1-2',
      ];

      parts.forEach((p, i) => {
        const rowY = 60 + i * 10;
        if (i === 0) {
          ctx.fillStyle = cYellow;
          ctx.fillRect(14, rowY - 1, 550, 9);
          ctx.fillStyle = cBlack;
          ctx.fillText(p, 16, rowY);
        } else {
          ctx.fillStyle = cWhite;
          ctx.fillText(p, 16, rowY);
        }
      });
    } else if (state.mode === 'SAMPLE') {
      ctx.fillStyle = cWhite;
      ctx.fillText('[SAMPLE WAVE]  W01: JP-8_BRASS_44K.WAV   (16-BIT MONO 44.1KHZ)', 16, 44);
      ctx.strokeStyle = cWhite;
      ctx.beginPath();
      ctx.moveTo(16, 54);
      ctx.lineTo(624, 54);
      ctx.stroke();

      ctx.fillText('SAMPLE LENGTH: 130,560 WORDS (2.95 SEC)  ORIGINAL KEY: C4', 20, 64);
      ctx.fillText('LOOP MODE:     FORWARD                   FINE TUNE:    +0', 20, 78);
      ctx.fillText('START POINT:   0000,000                  END POINT:    0130,560', 20, 92);
      ctx.fillText('LOOP START:    0048,200                  LOOP END:     0128,400', 20, 106);

      // Draw Waveform visualizer
      ctx.strokeStyle = cYellow;
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 20; x < 480; x++) {
        const mid = 160;
        const amp = 20.0 * Math.sin((x - 20) * 0.15) * Math.cos((x - 20) * 0.04);
        if (x === 20) ctx.moveTo(x, mid + amp);
        else ctx.lineTo(x, mid + amp);
      }
      ctx.stroke();
    } else {
      ctx.fillStyle = cWhite;
      ctx.fillText('[SYSTEM SETUP]  ROLAND S-760 SYSTEM VERSION 2.24', 16, 44);
      ctx.strokeStyle = cWhite;
      ctx.beginPath();
      ctx.moveTo(16, 54);
      ctx.lineTo(624, 54);
      ctx.stroke();

      ctx.fillText('1. HOST SCSI ID:     [ 7 ] (S-760 INITIATOR ID)', 20, 58);
      ctx.fillText('2. BOOT DEVICE:      [ SCSI / FLOPPY AUTO-DETECT ]', 20, 70);
      ctx.fillStyle = cYellow;
      ctx.fillText('3. SCSI BUS SCAN:    (BLUESCSI / ZULUSCSI TARGETS 0-6):', 20, 82);
      ctx.fillStyle = cGreen;
      ctx.fillText('   ID 0: APPLE CD-ROM 300+ (OPTICAL DRIVE)', 20, 94);
      ctx.fillText('   ID 1: QUANTUM FIREBALL 1080S (1.08 GB HDD)', 20, 105);
      ctx.fillStyle = cWhite;
      ctx.fillText('   ID 2: --- NO DEVICE ---', 20, 116);
      ctx.fillText('   ID 3: --- NO DEVICE ---', 20, 127);
      ctx.fillText('   ID 4: --- NO DEVICE ---', 20, 138);
      ctx.fillText('   ID 5: --- NO DEVICE ---', 20, 149);
      ctx.fillText('   ID 6: --- NO DEVICE ---', 20, 160);
      ctx.fillText('4. MASTER TUNE:      [ 440.0 HZ ]  OUTPUT LEVEL: [ +4 DBU ]', 20, 174);
      ctx.fillText('5. WAVE MEMORY:      [ 32 MBYTES OK (2X 16MB SIMM) ]', 20, 186);
      ctx.fillText('6. OPTION BOARD:     [ OP-760-2 VIDEO BOARD INSTALLED ]', 20, 198);
    }

    // 6. Bottom Context Ribbon (White Background y = 222..239)
    ctx.fillStyle = cWhite;
    ctx.fillRect(0, 222, W, 18);

    ctx.fillStyle = cBlack;
    ctx.font = 'bold 9px monospace';
    ctx.fillText('ALLON', 20, 226);
    ctx.fillText('CONVLD', 170, 226);
    ctx.fillText('ON OFF', 330, 226);
    ctx.fillText('VOLINFO', 470, 226);

    // 7. Draw Mouse Crosshair Cursor at mousePos
    const { x, y } = mousePos;
    ctx.strokeStyle = cWhite;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x - 5, y);
    ctx.lineTo(x + 5, y);
    ctx.moveTo(x, y - 5);
    ctx.lineTo(x, y + 5);
    ctx.stroke();

  }, [state, currentDisk, mousePos]);

  return (
    <div className="relative flex flex-col items-center select-none">
      {/* 640x240 Aspect Ratio Container (8:3 native ratio matching OP-760 Color CRT) */}
      <div
        className="relative overflow-hidden rounded-[4px] bg-black border-2 border-neutral-700 shadow-[0_15px_40px_rgba(0,0,0,0.9),inset_0_0_15px_rgba(0,0,0,0.8)]"
        style={{
          width: '960px',
          height: '360px',
        }}
      >
        <canvas
          ref={canvasRef}
          width={640}
          height={240}
          onMouseMove={handleMouseMove}
          onClick={handleCanvasClick}
          className="w-full h-full cursor-crosshair block"
        />

        {/* CRT Scanline Overlay */}
        <div
          className="absolute inset-0 pointer-events-none opacity-20"
          style={{
            background:
              'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.35) 50%)',
            backgroundSize: '100% 2px',
          }}
        />

        {/* Subtle Glass Curvature Highlight */}
        <div
          className="absolute inset-0 pointer-events-none opacity-15"
          style={{
            background:
              'radial-gradient(ellipse at 50% 30%, rgba(255, 255, 255, 0.3) 0%, rgba(0, 0, 0, 0.5) 100%)',
          }}
        />
      </div>
    </div>
  );
};
