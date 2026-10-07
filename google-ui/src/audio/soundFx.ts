/**
 * Web Audio API synthesizer for vintage hardware tactile clicks,
 * Gotek/floppy stepper motor seek chirps, and Roland S-760 sample audition synthesis.
 */

class SoundFxEngine {
  private ctx: AudioContext | null = null;
  private soundEnabled: boolean = true;
  private floppySeekEnabled: boolean = true;
  private masterVolume: number = 0.8;

  constructor() {
    // AudioContext will be initialized on first user interaction
  }

  private initCtx() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
    return this.ctx;
  }

  public setSoundEnabled(enabled: boolean) {
    this.soundEnabled = enabled;
  }

  public isSoundEnabled(): boolean {
    return this.soundEnabled;
  }

  public setFloppySeekEnabled(enabled: boolean) {
    this.floppySeekEnabled = enabled;
  }

  public isFloppySeekEnabled(): boolean {
    return this.floppySeekEnabled;
  }

  public setVolume(vol: number) {
    this.masterVolume = Math.max(0, Math.min(1, vol));
  }

  /**
   * Tactile hardware switch click
   */
  public playClick(type: 'button' | 'rubber' | 'dial' | 'gotek_dial' | 'power' | 'eject') {
    if (!this.soundEnabled) return;
    const ctx = this.initCtx();
    if (!ctx) return;

    const now = ctx.currentTime;
    const gainNode = ctx.createGain();
    gainNode.connect(ctx.destination);

    if (type === 'button') {
      // Crisp mechanical tactile click
      const osc = ctx.createOscillator();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(1400, now);
      osc.frequency.exponentialRampToValueAtTime(120, now + 0.015);

      gainNode.gain.setValueAtTime(0.18 * this.masterVolume, now);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.02);

      osc.connect(gainNode);
      osc.start(now);
      osc.stop(now + 0.02);

      // Add tiny high-frequency contact snap
      const snap = ctx.createOscillator();
      snap.type = 'sine';
      snap.frequency.setValueAtTime(3200, now);
      const snapGain = ctx.createGain();
      snapGain.gain.setValueAtTime(0.12 * this.masterVolume, now);
      snapGain.gain.exponentialRampToValueAtTime(0.001, now + 0.008);
      snap.connect(snapGain);
      snapGain.connect(ctx.destination);
      snap.start(now);
      snap.stop(now + 0.008);

    } else if (type === 'rubber') {
      // Soft rubber dome thud
      const osc = ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(350, now);
      osc.frequency.exponentialRampToValueAtTime(60, now + 0.025);

      gainNode.gain.setValueAtTime(0.22 * this.masterVolume, now);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.03);

      osc.connect(gainNode);
      osc.start(now);
      osc.stop(now + 0.03);

    } else if (type === 'dial' || type === 'gotek_dial') {
      // Light rotary detent tick
      const osc = ctx.createOscillator();
      osc.type = 'square';
      osc.frequency.setValueAtTime(type === 'gotek_dial' ? 1900 : 1200, now);

      gainNode.gain.setValueAtTime(0.08 * this.masterVolume, now);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.009);

      // bandpass filter for metallic detent character
      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(2400, now);
      filter.Q.setValueAtTime(3, now);

      osc.connect(filter);
      filter.connect(gainNode);
      osc.start(now);
      osc.stop(now + 0.01);

    } else if (type === 'power') {
      // Heavy mechanical AC toggle switch clack
      const osc1 = ctx.createOscillator();
      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(280, now);
      osc1.frequency.exponentialRampToValueAtTime(40, now + 0.045);

      gainNode.gain.setValueAtTime(0.35 * this.masterVolume, now);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

      const filter = ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(600, now);

      osc1.connect(filter);
      filter.connect(gainNode);
      osc1.start(now);
      osc1.stop(now + 0.05);

    } else if (type === 'eject') {
      // USB insert/eject friction click
      const osc = ctx.createOscillator();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(220, now + 0.03);
      gainNode.gain.setValueAtTime(0.15 * this.masterVolume, now);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.03);
      osc.connect(gainNode);
      osc.start(now);
      osc.stop(now + 0.03);
    }
  }

  /**
   * Gotek / Floppy Head Stepper Motor Seek Chirps
   * Authentic multi-step chrrk... chrk... sound during image mount / track access
   */
  public playFloppySeekSound() {
    if (!this.soundEnabled || !this.floppySeekEnabled) return;
    const ctx = this.initCtx();
    if (!ctx) return;

    const baseTime = ctx.currentTime;
    const steps = 14;

    for (let i = 0; i < steps; i++) {
      const stepTime = baseTime + i * (0.016 + Math.random() * 0.014);
      const osc = ctx.createOscillator();
      osc.type = 'square';
      osc.frequency.setValueAtTime(420 + Math.random() * 260, stepTime);

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.05 * this.masterVolume, stepTime);
      gain.gain.exponentialRampToValueAtTime(0.001, stepTime + 0.012);

      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(1400 + Math.random() * 400, stepTime);
      filter.Q.setValueAtTime(4, stepTime);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(stepTime);
      osc.stop(stepTime + 0.015);
    }

    // Disk read completion double-beep chime
    const beepTime = baseTime + 0.32;
    const beep = ctx.createOscillator();
    beep.type = 'sine';
    beep.frequency.setValueAtTime(1800, beepTime);
    beep.frequency.setValueAtTime(2400, beepTime + 0.04);

    const beepGain = ctx.createGain();
    beepGain.gain.setValueAtTime(0.06 * this.masterVolume, beepTime);
    beepGain.gain.exponentialRampToValueAtTime(0.001, beepTime + 0.09);

    beep.connect(beepGain);
    beepGain.connect(ctx.destination);
    beep.start(beepTime);
    beep.stop(beepTime + 0.09);
  }

  /**
   * Roland S-760 Sample Audition Generator
   * Synthesizes 24-bit Roland style patches (Strings, Brass, Pad, Bass, Piano, 909)
   */
  public auditionSample(patchName: string, midiNote: number = 60, duration: number = 0.8) {
    if (!this.soundEnabled) return;
    const ctx = this.initCtx();
    if (!ctx) return;

    const now = ctx.currentTime;
    const freq = 440 * Math.pow(2, (midiNote - 69) / 12);

    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(0.24 * this.masterVolume, now);
    masterGain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
    masterGain.connect(ctx.destination);

    const filter = ctx.createBiquadFilter();
    filter.connect(masterGain);

    if (patchName.toLowerCase().includes('string') || patchName.toLowerCase().includes('pad')) {
      // Luscious 2-osc detuned saw with Roland TVF lowpass
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(1600, now);
      filter.frequency.exponentialRampToValueAtTime(900, now + duration);
      filter.Q.setValueAtTime(2.5, now);

      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      osc1.type = 'sawtooth';
      osc2.type = 'sawtooth';
      osc1.frequency.setValueAtTime(freq, now);
      osc2.frequency.setValueAtTime(freq * 1.006, now); // Detune +10 cents

      osc1.connect(filter);
      osc2.connect(filter);
      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + duration);
      osc2.stop(now + duration);

    } else if (patchName.toLowerCase().includes('brass')) {
      // Brassy filter envelope swell
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(450, now);
      filter.frequency.exponentialRampToValueAtTime(2800, now + 0.08);
      filter.frequency.exponentialRampToValueAtTime(1200, now + duration);
      filter.Q.setValueAtTime(3.8, now);

      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      osc1.type = 'sawtooth';
      osc2.type = 'sawtooth';
      osc1.frequency.setValueAtTime(freq, now);
      osc2.frequency.setValueAtTime(freq * 1.004, now);

      osc1.connect(filter);
      osc2.connect(filter);
      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + duration);
      osc2.stop(now + duration);

    } else if (patchName.toLowerCase().includes('bass')) {
      // Deep punchy analog synth/slap bass
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(2400, now);
      filter.frequency.exponentialRampToValueAtTime(220, now + 0.18);
      filter.Q.setValueAtTime(5, now);

      const osc = ctx.createOscillator();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq / 2, now); // Sub octave

      const sub = ctx.createOscillator();
      sub.type = 'sine';
      sub.frequency.setValueAtTime(freq / 2, now);

      osc.connect(filter);
      sub.connect(masterGain);
      osc.start(now);
      sub.start(now);
      osc.stop(now + duration);
      sub.stop(now + duration);

    } else if (patchName.toLowerCase().includes('909') || patchName.toLowerCase().includes('drum')) {
      // 909 Kick & Snare pop
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(3200, now);

      const osc = ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(140, now);
      osc.frequency.exponentialRampToValueAtTime(45, now + 0.2);

      const kickGain = ctx.createGain();
      kickGain.gain.setValueAtTime(0.4 * this.masterVolume, now);
      kickGain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

      osc.connect(kickGain);
      kickGain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.35);

    } else {
      // Default warm Roland acoustic piano / multi-sample
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(2600, now);
      filter.frequency.exponentialRampToValueAtTime(600, now + duration);

      const osc = ctx.createOscillator();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, now);

      const osc2 = ctx.createOscillator();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(freq * 2, now);

      const g2 = ctx.createGain();
      g2.gain.setValueAtTime(0.15, now);
      g2.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

      osc.connect(filter);
      osc2.connect(g2);
      g2.connect(filter);

      osc.start(now);
      osc2.start(now);
      osc.stop(now + duration);
      osc2.stop(now + duration);
    }
  }
}

export const soundFx = new SoundFxEngine();
