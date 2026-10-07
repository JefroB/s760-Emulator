import React from 'react';

interface RackEarProps {
  side: 'left' | 'right';
}

export const RackEar: React.FC<RackEarProps> = ({ side }) => {
  return (
    <div
      className={`relative flex flex-col justify-between items-center py-2 h-full select-none ${
        side === 'left'
          ? 'border-r border-neutral-700/80 shadow-[1px_0_3px_rgba(0,0,0,0.8)]'
          : 'border-l border-neutral-700/80 shadow-[-1px_0_3px_rgba(0,0,0,0.8)]'
      }`}
      style={{
        width: '44px',
        background:
          'linear-gradient(180deg, #2b2e34 0%, #1c1d21 40%, #151619 60%, #25282e 100%)',
      }}
    >
      {/* Top Rack Screw Cutout */}
      <RackScrewSlot />

      {/* Center 1U Stamping / Ear Seam Marker */}
      <div className="flex flex-col items-center gap-0.5 opacity-60">
        <div className="w-4 h-[1px] bg-neutral-400" />
        <span className="text-[7px] font-mono text-neutral-400 font-bold tracking-tighter">
          1U
        </span>
        <div className="w-4 h-[1px] bg-neutral-400" />
      </div>

      {/* Bottom Rack Screw Cutout */}
      <RackScrewSlot />
    </div>
  );
};

const RackScrewSlot: React.FC = () => {
  return (
    <div className="relative flex items-center justify-center w-7 h-5">
      {/* Oval cut-out indentation with metallic chamfer */}
      <div className="w-6 h-4 rounded-[4px] bg-gradient-to-b from-[#0a0b0d] to-[#181a1f] border border-neutral-700/80 shadow-[inset_0_2px_3px_rgba(0,0,0,0.9),0_1px_1px_rgba(255,255,255,0.08)] flex items-center justify-center">
        {/* Metallic Washer */}
        <div className="w-4 h-3.5 rounded-full bg-gradient-to-tr from-neutral-500 via-neutral-300 to-neutral-600 border border-neutral-600 shadow-sm flex items-center justify-center">
          {/* Countersunk Phillips/Hex screw head */}
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-neutral-700 via-neutral-850 to-neutral-900 border border-neutral-600 shadow-inner relative flex items-center justify-center">
            {/* Cross/Phillips slot */}
            <div className="w-2 h-[1px] bg-neutral-400" />
            <div className="h-2 w-[1px] bg-neutral-400 absolute" />
          </div>
        </div>
      </div>
    </div>
  );
};
