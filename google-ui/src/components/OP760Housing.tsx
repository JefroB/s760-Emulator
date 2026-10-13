import type {ReactNode} from 'react';

/** Shared physical monitor housing for both native entrypoints. */
export function OP760Housing({children,powerOn=true}:{children:ReactNode;powerOn?:boolean}) {
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
            {children}

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
              <span className={`w-2 h-2 rounded-full ${powerOn ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-neutral-700'}`} />
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
}
