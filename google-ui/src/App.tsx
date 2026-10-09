/**
 * Roland S-760 Digital Sampler Studio Interface
 * OP-760 Color CRT Monitor + 1U Rack Chassis with FlashFloppy Gotek OLED Mod
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  SamplerState,
  SamplerMode,
  DiskImage,
  HardwareEvent,
  DEFAULT_DISK_IMAGES,
} from './types/sampler';
import { OP760Monitor } from './components/OP760Monitor';
import { S760FrontPanel } from './components/S760FrontPanel';
import { soundFx } from './audio/soundFx';
import { BridgeProvider } from './bridge/BridgeContext';

export default function App() {
  const [diskList, setDiskList] = useState<DiskImage[]>(DEFAULT_DISK_IMAGES);

  const [state, setState] = useState<SamplerState>({
    powerOn: true,
    volume: 85,
    volumeAngle: 45, // roughly 85%
    alphaDialAngle: 0,
    mode: 'DISK',
    subMode: 'PLAY',
    activeCursorField: 0,
    cursorRow: 0,
    cursorCol: 0,
    backlightColor: 'emerald',

    currentPatchIndex: 0,
    currentPerfIndex: 0,
    sampleZoom: 1,
    sampleScrub: 25,

    gotek: {
      selectedImageIndex: 1, // Start on Strings disk
      mountedImageIndex: 1,
      isBusy: false,
      currentTrack: 18,
      currentSide: 0,
      usbInserted: true,
      dialAngle: 0,
      statusText: 'READY',
    },

    peakL: false,
    peakR: false,
    midiRx: false,
  });

  const [events, setEvents] = useState<HardwareEvent[]>([]);
  const seekTimerRef = useRef<number | null>(null);

  // Central Event Emitter & Window CustomEvent dispatcher
  const emitHardwareEvent = useCallback(
    (type: string, payload: Record<string, any> = {}, source: HardwareEvent['source'] = 'FRONT_PANEL') => {
      const now = new Date();
      const timeStr = `${now.toTimeString().split(' ')[0]}.${now.getMilliseconds().toString().padStart(3, '0')}`;
      const newEvent: HardwareEvent = {
        id: `ev_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        timestamp: timeStr,
        source,
        type,
        payload,
      };

      setEvents((prev) => [newEvent, ...prev.slice(0, 49)]);

      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new CustomEvent('s760_input', {
            detail: { type, payload, timestamp: timeStr },
          })
        );
      }
    },
    []
  );

  // Power Toggle
  const handleTogglePower = useCallback(() => {
    setState((prev) => {
      const nextPower = !prev.powerOn;
      return {
        ...prev,
        powerOn: nextPower,
      };
    });
    emitHardwareEvent('POWER_STATE_CHANGE', { powerOn: !state.powerOn });
  }, [emitHardwareEvent, state.powerOn]);

  // Master Volume Change
  const handleSetVolume = useCallback(
    (vol: number) => {
      const clamped = Math.max(0, Math.min(100, vol));
      const angle = -135 + (clamped / 100) * 270;
      soundFx.setVolume(clamped / 100);
      setState((prev) => ({
        ...prev,
        volume: clamped,
        volumeAngle: angle,
      }));
      emitHardwareEvent('VOLUME_CHANGE', { volume: clamped });
    },
    [emitHardwareEvent]
  );

  // Mode Selection
  const handleSetMode = useCallback(
    (mode: SamplerMode) => {
      setState((prev) => ({
        ...prev,
        mode,
        activeCursorField: 0,
      }));
      emitHardwareEvent('MODE_CHANGE', { mode });
    },
    [emitHardwareEvent]
  );

  // Alpha Dial Turn
  const handleAlphaDialStep = useCallback(
    (delta: number) => {
      setState((prev) => {
        const newAngle = (prev.alphaDialAngle + delta * 15) % 360;

        if (prev.mode === 'SAMPLE') {
          const newScrub = Math.max(0, Math.min(100, prev.sampleScrub + delta * 2));
          return {
            ...prev,
            alphaDialAngle: newAngle,
            sampleScrub: newScrub,
          };
        }

        const newPatch = Math.max(0, (prev.currentPatchIndex + delta + 16) % 16);
        return {
          ...prev,
          alphaDialAngle: newAngle,
          currentPatchIndex: newPatch,
        };
      });

      emitHardwareEvent('ALPHA_DIAL_STEP', { delta });
    },
    [emitHardwareEvent]
  );

  // Navigation Keys
  const handleNavigate = useCallback(
    (dir: 'UP' | 'DOWN' | 'LEFT' | 'RIGHT') => {
      setState((prev) => {
        let field = prev.activeCursorField;
        if (dir === 'DOWN' || dir === 'RIGHT') field = (field + 1) % 4;
        if (dir === 'UP' || dir === 'LEFT') field = (field - 1 + 4) % 4;
        return {
          ...prev,
          activeCursorField: field,
        };
      });
      emitHardwareEvent('NAV_KEY', { direction: dir });
    },
    [emitHardwareEvent]
  );

  // Inc / Dec Buttons
  const handleIncDec = useCallback(
    (delta: number) => {
      handleAlphaDialStep(delta);
      emitHardwareEvent('INC_DEC_BUTTON', { delta });
    },
    [handleAlphaDialStep, emitHardwareEvent]
  );

  // Gotek Mount / Load Operation
  const handleMountDisk = useCallback(() => {
    if (!state.gotek.usbInserted) return;

    if (seekTimerRef.current !== null) {
      clearInterval(seekTimerRef.current);
    }

    setState((prev) => ({
      ...prev,
      gotek: {
        ...prev.gotek,
        isBusy: true,
        currentTrack: 0,
        statusText: 'READING...',
      },
    }));

    soundFx.playFloppySeekSound();

    let trk = 0;
    seekTimerRef.current = window.setInterval(() => {
      trk += 4;
      if (trk >= 80) {
        if (seekTimerRef.current !== null) {
          clearInterval(seekTimerRef.current);
          seekTimerRef.current = null;
        }
        setState((prev) => ({
          ...prev,
          currentPatchIndex: 0,
          gotek: {
            ...prev.gotek,
            isBusy: false,
            mountedImageIndex: prev.gotek.selectedImageIndex,
            currentTrack: 0,
            statusText: 'READY',
          },
        }));
        emitHardwareEvent('GOTEK_MOUNT_COMPLETE', {
          mountedDisk: diskList[state.gotek.selectedImageIndex]?.filename,
        });
      } else {
        setState((prev) => ({
          ...prev,
          gotek: {
            ...prev.gotek,
            currentTrack: trk,
          },
        }));
        if (trk % 12 === 0) {
          soundFx.playFloppySeekSound();
        }
      }
    }, 90);
  }, [diskList, emitHardwareEvent, state.gotek.selectedImageIndex, state.gotek.usbInserted]);

  // Toggle USB Flash Drive
  const handleToggleUsb = useCallback(() => {
    const nextInserted = !state.gotek.usbInserted;
    soundFx.playClick('button');
    emitHardwareEvent('GOTEK_USB_TOGGLE', { inserted: nextInserted });

    setState((prev) => ({
      ...prev,
      gotek: {
        ...prev.gotek,
        usbInserted: nextInserted,
        mountedImageIndex: nextInserted ? prev.gotek.mountedImageIndex : null,
        statusText: nextInserted ? 'READY' : 'NO USB',
      },
    }));
  }, [emitHardwareEvent, state.gotek.usbInserted]);

  // Audition Patch Sound
  const triggerAudition = useCallback(() => {
    if (!state.powerOn) return;
    const currentDisk =
      state.gotek.mountedImageIndex !== null
        ? diskList[state.gotek.mountedImageIndex]
        : diskList[state.gotek.selectedImageIndex];
    const patchName =
      currentDisk?.patches[state.currentPatchIndex % currentDisk.patches.length] || 'Default';

    soundFx.auditionSample(patchName, 60 + (state.currentPatchIndex % 12));

    setState((prev) => ({ ...prev, peakL: true, peakR: true, midiRx: true }));
    setTimeout(() => {
      setState((prev) => ({ ...prev, peakL: false, peakR: false, midiRx: false }));
    }, 180);

    emitHardwareEvent('AUDITION_TRIGGER', { patch: patchName });
  }, [diskList, emitHardwareEvent, state.currentPatchIndex, state.gotek.mountedImageIndex, state.gotek.selectedImageIndex, state.powerOn, state.volume]);

  // Enter Button
  const handleEnter = useCallback(() => {
    emitHardwareEvent('ENTER_KEY', { mode: state.mode });
    if (state.mode === 'DISK') {
      handleMountDisk();
    }
  }, [emitHardwareEvent, state.mode, handleMountDisk]);

  // Exit Button
  const handleExit = useCallback(() => {
    setState((prev) => ({ ...prev, mode: 'PERF' }));
    emitHardwareEvent('EXIT_KEY', {});
  }, [emitHardwareEvent]);

  // Soft Function Keys [F1] to [F6]
  const handleSoftKey = useCallback(
    (fIndex: number) => {
      emitHardwareEvent('SOFT_KEY', { key: `F${fIndex + 1}`, mode: state.mode });

      if (state.mode === 'SAMPLE') {
        if (fIndex === 0) {
          triggerAudition();
          return;
        }
        if (fIndex === 1) {
          setState((prev) => ({
            ...prev,
            sampleZoom: prev.sampleZoom === 1 ? 4 : prev.sampleZoom === 4 ? 16 : 1,
          }));
          return;
        }
      } else if (state.mode === 'DISK') {
        if (fIndex === 0) {
          handleMountDisk();
          return;
        }
        if (fIndex === 4) {
          handleToggleUsb();
          return;
        }
      } else if (state.mode === 'SYSTEM') {
        if (fIndex === 3) {
          setState((prev) => ({
            ...prev,
            backlightColor: prev.backlightColor === 'emerald' ? 'amber' : 'emerald',
          }));
          return;
        }
      }
    },
    [emitHardwareEvent, state.mode, triggerAudition, handleMountDisk, handleToggleUsb]
  );

  // Gotek Disk Selection
  const handleSelectDiskIndex = useCallback(
    (idx: number) => {
      setState((prev) => ({
        ...prev,
        gotek: {
          ...prev.gotek,
          selectedImageIndex: idx,
        },
      }));
      emitHardwareEvent('GOTEK_SELECT_DISK', {
        index: idx,
        disk: diskList[idx]?.filename,
      });
    },
    [diskList, emitHardwareEvent]
  );

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.code === 'Space') {
        e.preventDefault();
        triggerAudition();
      } else if (e.code === 'ArrowUp') {
        e.preventDefault();
        handleNavigate('UP');
      } else if (e.code === 'ArrowDown') {
        e.preventDefault();
        handleNavigate('DOWN');
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        handleNavigate('LEFT');
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        handleNavigate('RIGHT');
      } else if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        handleIncDec(1);
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        handleIncDec(-1);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        handleEnter();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        handleExit();
      } else if (e.key === '[') {
        e.preventDefault();
        handleSelectDiskIndex((state.gotek.selectedImageIndex - 1 + diskList.length) % diskList.length);
      } else if (e.key === ']') {
        e.preventDefault();
        handleSelectDiskIndex((state.gotek.selectedImageIndex + 1) % diskList.length);
      } else if (e.key === '\\') {
        e.preventDefault();
        handleMountDisk();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [diskList.length, handleEnter, handleExit, handleIncDec, handleMountDisk, handleNavigate, handleSelectDiskIndex, state.gotek.selectedImageIndex, triggerAudition]);

  return (
    <BridgeProvider>
    <div className="min-h-screen bg-[#0a0c0f] text-neutral-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Header Bar */}
      <header className="flex items-center justify-between px-6 py-2.5 border-b border-neutral-800 bg-[#101216] shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-sm font-black tracking-wider text-neutral-100 uppercase font-mono">
            S-760 Studio Suite
          </span>
          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/70 px-2 py-0.5 rounded border border-cyan-800/60">
            FlashFloppy Gotek OLED Mod
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={triggerAudition}
            className="px-3 py-1.5 text-xs font-mono font-semibold bg-emerald-800/80 hover:bg-emerald-700 text-emerald-100 rounded border border-emerald-600 transition-colors whitespace-nowrap flex items-center gap-1.5 cursor-pointer"
          >
            <span className={`w-2 h-2 rounded-full ${state.midiRx ? 'bg-emerald-300 animate-ping' : 'bg-emerald-500'}`} />
            Audition Patch [Space]
          </button>
        </div>
      </header>

      {/* Main Studio Stack: OP-760 Color CRT Monitor on Top + 1U Rack Faceplate Below */}
      <main className="flex-1 flex flex-col items-center justify-center p-4 lg:p-6 gap-5 overflow-x-hidden">
        {/* Top: OP-760 Color CRT Monitor */}
        <OP760Monitor
          state={state}
          diskList={diskList}
          onSetMode={handleSetMode}
          onSoftKey={handleSoftKey}
          onSelectPatchIndex={(idx) => {
            setState((prev) => ({ ...prev, currentPatchIndex: idx }));
            soundFx.playClick('button');
          }}
          onEventEmit={emitHardwareEvent}
        />

        {/* Bottom: Roland S-760 1U Rack-Mount Hardware Front Panel */}
        <div className="w-full max-w-[1480px] overflow-x-auto flex justify-center py-2">
          <S760FrontPanel
            state={state}
            diskList={diskList}
            onTogglePower={handleTogglePower}
            onSetVolume={handleSetVolume}
            onSetMode={handleSetMode}
            onAlphaDialStep={handleAlphaDialStep}
            onNavigate={handleNavigate}
            onIncDec={handleIncDec}
            onEnter={handleEnter}
            onExit={handleExit}
            onSoftKey={handleSoftKey}
            onSelectDiskIndex={handleSelectDiskIndex}
            onMountDisk={handleMountDisk}
            onToggleUsb={handleToggleUsb}
            onEventEmit={emitHardwareEvent}
            onTriggerAudition={triggerAudition}
          />
        </div>
      </main>
    </div>
    </BridgeProvider>
  );
}
