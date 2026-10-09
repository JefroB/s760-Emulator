import React, { useState } from 'react';
import { HardwareEvent, DiskImage, SamplerMode } from '../types/sampler';
import { soundFx } from '../audio/soundFx';
import { useBridgeStatus, useBridgeTelemetry, useBridgeClient } from '../bridge/BridgeContext';
import { DEFAULT_BRIDGE_URL } from '../bridge/S760BridgeClient';

interface EmulatorBridgePanelProps {
  events: HardwareEvent[];
  diskList: DiskImage[];
  selectedDiskIndex: number;
  mountedDiskIndex: number | null;
  backlightColor: 'emerald' | 'amber';
  onClearEvents: () => void;
  onAddCustomDisk: (disk: DiskImage) => void;
  onSetBacklightColor: (color: 'emerald' | 'amber') => void;
  onMountDiskIndex: (idx: number) => void;
  onSelectDiskIndex: (idx: number) => void;
  onEventEmit: (type: string, payload: any) => void;
}

export const EmulatorBridgePanel: React.FC<EmulatorBridgePanelProps> = ({
  events,
  diskList,
  selectedDiskIndex,
  mountedDiskIndex,
  backlightColor,
  onClearEvents,
  onAddCustomDisk,
  onSetBacklightColor,
  onMountDiskIndex,
  onSelectDiskIndex,
  onEventEmit,
}) => {
  const [activeTab, setActiveTab] = useState<'events' | 'disks' | 'bridge' | 'settings'>('events');
  const [soundEnabled, setSoundEnabled] = useState(soundFx.isSoundEnabled());

  // Live bridge connection state (low-rate React state only — never per-pixel).
  const bridgeStatus = useBridgeStatus();
  const telemetry = useBridgeTelemetry();
  const bridgeClient = useBridgeClient();
  const [seekEnabled, setSeekEnabled] = useState(soundFx.isFloppySeekEnabled());
  const [copied, setCopied] = useState(false);

  // New Disk Form State
  const [newDiskName, setNewDiskName] = useState('');
  const [newDiskLabel, setNewDiskLabel] = useState('');

  const handleToggleSound = () => {
    const next = !soundEnabled;
    soundFx.setSoundEnabled(next);
    setSoundEnabled(next);
  };

  const handleToggleSeek = () => {
    const next = !seekEnabled;
    soundFx.setFloppySeekEnabled(next);
    setSeekEnabled(next);
  };

  const handleCreateCustomDisk = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDiskName.trim()) return;

    const slotNum = (diskList.length + 1).toString().padStart(3, '0');
    const filename = newDiskName.trim().toUpperCase().endsWith('.IMG')
      ? newDiskName.trim().toUpperCase()
      : `${newDiskName.trim().toUpperCase()}.IMG`;

    const customDisk: DiskImage = {
      id: `custom_${Date.now()}`,
      slot: `${slotNum}/084`,
      filename,
      folder: '/ROLAND/',
      label: newDiskLabel.trim() || `User Bank ${filename}`,
      sizeKb: 1440,
      format: 'IMG',
      patches: ['01 Custom Patch A', '02 Custom Patch B', '03 Raw Waveform', '04 Drum Map'],
      sampleWaveformType: 'synth',
      sampleRate: '44.1kHz',
      samplePoints: { start: 0, loopStart: 12000, loopEnd: 44100, totalSamples: 44100 },
    };

    onAddCustomDisk(customDisk);
    setNewDiskName('');
    setNewDiskLabel('');
    onEventEmit('CUSTOM_DISK_ADDED', { filename, slot: customDisk.slot });
  };

  const copyEventStream = () => {
    const text = JSON.stringify(events.slice(0, 30), null, 2);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full max-w-7xl mx-auto mt-6 bg-neutral-900 border border-neutral-800 rounded-lg shadow-xl overflow-hidden flex flex-col">
      {/* Tab Navigation Header */}
      <div className="flex items-center justify-between border-b border-neutral-800 px-4 py-2.5 bg-neutral-950/70">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold text-neutral-200 tracking-wider">
            S-760 EMULATOR BRIDGE &amp; INTEGRATION BUS
          </span>
          {/* Live connection indicator driven by the real bridge status (R6.4). */}
          <span
            className={`flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded border ${
              bridgeStatus === 'connected'
                ? 'text-emerald-400 bg-emerald-950/50 border-emerald-800/40'
                : bridgeStatus === 'connecting'
                ? 'text-amber-400 bg-amber-950/50 border-amber-800/40'
                : 'text-neutral-400 bg-neutral-800/50 border-neutral-700/50'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                bridgeStatus === 'connected'
                  ? 'bg-emerald-400 shadow-[0_0_6px_#34d399]'
                  : bridgeStatus === 'connecting'
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-neutral-500'
              }`}
            />
            {bridgeStatus === 'connected'
              ? 'BRIDGE LIVE'
              : bridgeStatus === 'connecting'
              ? 'CONNECTING'
              : 'OFFLINE'}
          </span>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center gap-1 bg-neutral-900 p-0.5 rounded border border-neutral-800">
          <button
            type="button"
            onClick={() => setActiveTab('events')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              activeTab === 'events'
                ? 'bg-neutral-800 text-neutral-100 font-semibold shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Hardware Events ({events.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('disks')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              activeTab === 'disks'
                ? 'bg-neutral-800 text-neutral-100 font-semibold shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Gotek Disk Library ({diskList.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('bridge')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              activeTab === 'bridge'
                ? 'bg-neutral-800 text-neutral-100 font-semibold shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Live Bridge
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('settings')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              activeTab === 'settings'
                ? 'bg-neutral-800 text-neutral-100 font-semibold shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Panel &amp; Audio Config
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="p-4 min-h-[220px]">
        {/* Tab 1: Hardware Event Stream */}
        {activeTab === 'events' && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-neutral-400">
                Real-time serial events dispatched on button press, dial turn, and Gotek swaps:
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={copyEventStream}
                  className="px-2.5 py-1 text-xs font-mono bg-neutral-800 hover:bg-neutral-750 text-neutral-300 rounded border border-neutral-700 transition-colors"
                >
                  {copied ? 'Copied to Clipboard' : 'Copy Event JSON'}
                </button>
                <button
                  type="button"
                  onClick={onClearEvents}
                  className="px-2.5 py-1 text-xs font-mono bg-neutral-800 hover:bg-neutral-750 text-neutral-300 rounded border border-neutral-700 transition-colors"
                >
                  Clear Log
                </button>
              </div>
            </div>

            {/* Event List Table */}
            <div className="max-h-60 overflow-y-auto rounded border border-neutral-800 bg-neutral-950 font-mono text-[11px]">
              {events.length === 0 ? (
                <div className="p-6 text-center text-neutral-500">
                  No hardware events recorded yet. Rotate the knobs or click front panel buttons!
                </div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-800 text-neutral-400 bg-neutral-900/60 text-[10px] uppercase">
                      <th className="py-1.5 px-3">Time</th>
                      <th className="py-1.5 px-3">Source</th>
                      <th className="py-1.5 px-3">Event Type</th>
                      <th className="py-1.5 px-3">Payload Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.slice(0, 40).map((ev) => (
                      <tr
                        key={ev.id}
                        className="border-b border-neutral-850 hover:bg-neutral-900/40 transition-colors"
                      >
                        <td className="py-1 px-3 text-neutral-500 whitespace-nowrap">
                          {ev.timestamp}
                        </td>
                        <td className="py-1 px-3">
                          <span
                            className={`text-[9.5px] px-1 py-0.5 rounded ${
                              ev.source === 'GOTEK'
                                ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/40'
                                : 'bg-neutral-800 text-neutral-300'
                            }`}
                          >
                            {ev.source}
                          </span>
                        </td>
                        <td className="py-1 px-3 font-semibold text-emerald-400">{ev.type}</td>
                        <td className="py-1 px-3 text-neutral-300 truncate max-w-xs">
                          {JSON.stringify(ev.payload)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Gotek Disk Image Library */}
        {activeTab === 'disks' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Disk Library Grid */}
            <div className="lg:col-span-2 flex flex-col gap-2">
              <span className="text-xs text-neutral-400">
                Loaded FlashFloppy Gotek USB Image Catalog (Click to select or mount directly):
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
                {diskList.map((disk, idx) => {
                  const isSelected = selectedDiskIndex === idx;
                  const isMounted = mountedDiskIndex === idx;
                  return (
                    <div
                      key={disk.id}
                      onClick={() => onSelectDiskIndex(idx)}
                      className={`p-2.5 rounded border cursor-pointer transition-all flex flex-col justify-between ${
                        isMounted
                          ? 'bg-cyan-950/40 border-cyan-500/60 shadow-[0_0_8px_rgba(6,182,212,0.15)]'
                          : isSelected
                          ? 'bg-neutral-800 border-neutral-600'
                          : 'bg-neutral-950/60 border-neutral-800 hover:border-neutral-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-neutral-200">
                          {disk.slot} {disk.filename}
                        </span>
                        {isMounted && (
                          <span className="text-[9px] font-mono font-bold text-cyan-300 bg-cyan-900/60 px-1.5 py-0.5 rounded">
                            MOUNTED
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-neutral-400 mt-1">{disk.label}</div>
                      <div className="flex items-center justify-between mt-2 pt-1 border-t border-neutral-800/80 text-[10px] font-mono text-neutral-500">
                        <span>
                          {disk.sizeKb}KB · {disk.format}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectDiskIndex(idx);
                            onMountDiskIndex(idx);
                          }}
                          className="px-2 py-0.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded border border-neutral-700"
                        >
                          Mount to Sampler
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Add Custom Disk Form */}
            <div className="flex flex-col gap-2 p-3 bg-neutral-950 rounded border border-neutral-800">
              <span className="text-xs font-mono font-bold text-neutral-200">
                + ADD CUSTOM DISK IMAGE
              </span>
              <p className="text-[11px] text-neutral-400">
                Simulate adding a new vintage sampler bank or converted AKAI/Roland disk image to
                the Gotek USB thumb drive.
              </p>
              <form onSubmit={handleCreateCustomDisk} className="flex flex-col gap-2 mt-1">
                <div>
                  <label className="text-[10px] font-mono text-neutral-400 block mb-1">
                    Filename (.IMG / .HFE / .DSK):
                  </label>
                  <input
                    type="text"
                    placeholder="MY_NEW_SAMPLES.IMG"
                    value={newDiskName}
                    onChange={(e) => setNewDiskName(e.target.value)}
                    className="w-full px-2 py-1 text-xs font-mono bg-neutral-900 border border-neutral-700 rounded text-neutral-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-mono text-neutral-400 block mb-1">
                    Catalog Description / Label:
                  </label>
                  <input
                    type="text"
                    placeholder="Custom 90s Drum & Bass Breaks"
                    value={newDiskLabel}
                    onChange={(e) => setNewDiskLabel(e.target.value)}
                    className="w-full px-2 py-1 text-xs font-mono bg-neutral-900 border border-neutral-700 rounded text-neutral-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <button
                  type="submit"
                  className="mt-2 py-1.5 px-3 text-xs font-mono font-semibold bg-cyan-700 hover:bg-cyan-600 text-white rounded transition-colors"
                >
                  Write Image to USB
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Tab 3: Live Bridge connection + status to the in-process C++ core */}
        {activeTab === 'bridge' && (
          <div className="flex flex-col gap-3">
            <span className="text-xs text-neutral-400">
              Live link to the in-process C++ <span className="font-mono">S760Bridge</span>. React
              composites the three authentic display surfaces (CRT / SED1335 LCD / Gotek OLED) it
              streams, and forwards front-panel input over one message contract.
            </span>

            {/* Connection status + controls */}
            <div className="flex items-center justify-between p-3 bg-neutral-950 rounded border border-neutral-800">
              <div className="flex items-center gap-3">
                <span
                  className={`flex items-center gap-2 text-sm font-mono font-bold ${
                    bridgeStatus === 'connected'
                      ? 'text-emerald-400'
                      : bridgeStatus === 'connecting'
                      ? 'text-amber-400'
                      : 'text-neutral-400'
                  }`}
                >
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      bridgeStatus === 'connected'
                        ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                        : bridgeStatus === 'connecting'
                        ? 'bg-amber-400 animate-pulse'
                        : 'bg-neutral-600'
                    }`}
                  />
                  {bridgeStatus === 'connected'
                    ? 'CONNECTED'
                    : bridgeStatus === 'connecting'
                    ? 'CONNECTING…'
                    : 'DISCONNECTED'}
                </span>
                <span className="text-[11px] font-mono text-neutral-500">
                  {DEFAULT_BRIDGE_URL}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => bridgeClient?.connect()}
                  disabled={!bridgeClient || bridgeStatus === 'connected'}
                  className="px-2.5 py-1 text-xs font-mono bg-neutral-800 hover:bg-neutral-700 disabled:opacity-40 disabled:cursor-not-allowed text-neutral-200 rounded border border-neutral-700 transition-colors"
                >
                  Connect
                </button>
                <button
                  type="button"
                  onClick={() => bridgeClient?.disconnect()}
                  disabled={!bridgeClient || bridgeStatus === 'disconnected'}
                  className="px-2.5 py-1 text-xs font-mono bg-neutral-800 hover:bg-neutral-700 disabled:opacity-40 disabled:cursor-not-allowed text-neutral-200 rounded border border-neutral-700 transition-colors"
                >
                  Disconnect
                </button>
              </div>
            </div>

            {/* Live telemetry (low-rate; pixels never travel through React state) */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { label: 'FPS', value: telemetry ? telemetry.fps.toFixed(0) : '—' },
                { label: 'Mode', value: telemetry?.currentMode || '—' },
                { label: 'Voices', value: telemetry ? String(telemetry.activeVoices) : '—' },
                {
                  label: 'Peak L/R',
                  value: telemetry
                    ? `${telemetry.peakL.toFixed(2)}/${telemetry.peakR.toFixed(2)}`
                    : '—',
                },
              ].map((cell) => (
                <div
                  key={cell.label}
                  className="flex flex-col gap-0.5 p-2.5 bg-neutral-950 rounded border border-neutral-800"
                >
                  <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500">
                    {cell.label}
                  </span>
                  <span className="text-sm font-mono font-bold text-emerald-400/90">
                    {cell.value}
                  </span>
                </div>
              ))}
            </div>

            {bridgeStatus !== 'connected' && (
              <div className="text-[11px] font-mono text-neutral-500 p-2 bg-neutral-950/60 rounded border border-neutral-800/60">
                No backend connected — the shell renders its offline/local display state and the
                client retries with backoff. Start the C++ <span className="font-mono">S760Bridge</span>{' '}
                standalone server to go live.
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Panel & Audio Config */}
        {activeTab === 'settings' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-3 p-3 bg-neutral-950 rounded border border-neutral-800">
              <span className="text-xs font-mono font-bold text-neutral-200">
                DISPLAY &amp; BACKLIGHT
              </span>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-neutral-300">160×64 LCD Backlight Tint</div>
                  <div className="text-[11px] text-neutral-500">
                    Switch between original Roland Emerald Green and Amber Warm LED
                  </div>
                </div>
                <div className="flex items-center gap-1 bg-neutral-900 p-1 rounded border border-neutral-700">
                  <button
                    type="button"
                    onClick={() => onSetBacklightColor('emerald')}
                    className={`px-2 py-1 text-xs font-mono rounded ${
                      backlightColor === 'emerald'
                        ? 'bg-emerald-600 text-white font-bold'
                        : 'text-neutral-400 hover:text-neutral-200'
                    }`}
                  >
                    Emerald
                  </button>
                  <button
                    type="button"
                    onClick={() => onSetBacklightColor('amber')}
                    className={`px-2 py-1 text-xs font-mono rounded ${
                      backlightColor === 'amber'
                        ? 'bg-amber-600 text-white font-bold'
                        : 'text-neutral-400 hover:text-neutral-200'
                    }`}
                  >
                    Amber
                  </button>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3 p-3 bg-neutral-950 rounded border border-neutral-800">
              <span className="text-xs font-mono font-bold text-neutral-200">
                HARDWARE AUDIO HAPTICS
              </span>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-neutral-300">Tactile Mechanical Clicks</div>
                  <div className="text-[11px] text-neutral-500">
                    Synthesized push-button relays, rocker switches &amp; encoder detents
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleToggleSound}
                  className={`px-3 py-1 text-xs font-mono rounded border transition-colors ${
                    soundEnabled
                      ? 'bg-emerald-800/80 text-emerald-200 border-emerald-600'
                      : 'bg-neutral-800 text-neutral-400 border-neutral-700'
                  }`}
                >
                  {soundEnabled ? 'Enabled' : 'Muted'}
                </button>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-neutral-850">
                <div>
                  <div className="text-xs text-neutral-300">Floppy Stepper Seek Audio</div>
                  <div className="text-[11px] text-neutral-500">
                    Vintage head seek chirps and motor spin when mounting disk images
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleToggleSeek}
                  className={`px-3 py-1 text-xs font-mono rounded border transition-colors ${
                    seekEnabled
                      ? 'bg-emerald-800/80 text-emerald-200 border-emerald-600'
                      : 'bg-neutral-800 text-neutral-400 border-neutral-700'
                  }`}
                >
                  {seekEnabled ? 'Enabled' : 'Muted'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
